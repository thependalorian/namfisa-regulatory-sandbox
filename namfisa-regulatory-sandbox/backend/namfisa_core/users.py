import uuid
import re
import hashlib
import secrets
from datetime import datetime, timedelta

from typing import Optional

from fastapi import Depends, Request, HTTPException, status
from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    UUIDIDMixin,
    InvalidPasswordException,
)

from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from .config import settings
from .database import get_user_db, get_async_session
from .email import send_reset_password_email
from .models import User, AuditTrail
from .schemas import UserCreate


# Enhanced authentication with PSD-12 compliance
async def authenticate_with_psd12_compliance(credentials, user_manager):
    """Enhanced authentication with PSD-12 compliance"""
    email = credentials.username if hasattr(credentials, 'username') else None
    password = credentials.password if hasattr(credentials, 'password') else None

    if not email or not password:
        return None

    user = await user_manager.authenticate_user(email, password)

    if user:
        # Update last login IP and time
        user.last_login_ip = getattr(credentials, 'request', {}).client.host if hasattr(credentials, 'request') else None
        await user_manager.user_db.update(user)

    return user if user else None

AUTH_URL_PATH = "auth"


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.RESET_PASSWORD_SECRET_KEY
    verification_token_secret = settings.VERIFICATION_SECRET_KEY

    # PSD-12 cybersecurity compliance settings
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=30)
    PASSWORD_COMPLEXITY_MIN_LENGTH = 12

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

        # PSD-12: Log registration event for audit
        await self._log_security_event(
            user_id=user.id,
            event_type="user_registration",
            ip_address=getattr(request, 'client', {}).host if request else None,
            user_agent=getattr(request, 'headers', {}).get('user-agent') if request else None
        )

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        await send_reset_password_email(user, token)

        # PSD-12: Log password reset request
        await self._log_security_event(
            user_id=user.id,
            event_type="password_reset_requested",
            ip_address=getattr(request, 'client', {}).host if request else None
        )

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

        # PSD-12: Log email verification request
        await self._log_security_event(
            user_id=user.id,
            event_type="email_verification_requested",
            ip_address=getattr(request, 'client', {}).host if request else None
        )

    async def validate_password(
        self,
        password: str,
        user: UserCreate,
    ) -> None:
        errors = []

        # Enhanced password requirements for PSD-12 compliance
        if len(password) < self.PASSWORD_COMPLEXITY_MIN_LENGTH:
            errors.append(f"Password should be at least {self.PASSWORD_COMPLEXITY_MIN_LENGTH} characters.")
        if user.email and user.email.lower() in password.lower():
            errors.append("Password should not contain e-mail address.")
        if not any(char.isupper() for char in password):
            errors.append("Password should contain at least one uppercase letter.")
        if not any(char.islower() for char in password):
            errors.append("Password should contain at least one lowercase letter.")
        if not any(char.isdigit() for char in password):
            errors.append("Password should contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password should contain at least one special character.")

        # Check for common weak passwords
        common_passwords = ["password", "123456", "qwerty", "admin", "letmein"]
        if password.lower() in common_passwords:
            errors.append("Password is too common and easily guessable.")

        if errors:
            raise InvalidPasswordException(reason=errors)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Enhanced authentication with PSD-12 compliance"""

        # Get user database session
        user_db = await get_user_db()
        user = await user_db.get_by_email(email)

        if not user:
            # Log failed login attempt (even for non-existent users)
            await self._log_security_event(
                event_type="failed_login",
                email=email,
                ip_address=None  # Will be set by middleware
            )
            return None

        # Check if account is locked
        if user.account_locked:
            # Check if lockout period has expired
            if user.last_login_ip and user.login_attempts >= self.MAX_LOGIN_ATTEMPTS:
                lockout_expiry = user.last_login_attempt + self.ACCOUNT_LOCKOUT_DURATION
                if datetime.utcnow() < lockout_expiry:
                    await self._log_security_event(
                        user_id=user.id,
                        event_type="account_lockout_attempt",
                        details={"reason": "Account locked due to multiple failed attempts"}
                    )
                    return None
                else:
                    # Reset lockout
                    user.account_locked = False
                    user.login_attempts = 0
                    await user_db.update(user)

        # Verify password
        valid_password, updated_hash = user.verify_password(password)

        if not valid_password:
            # Increment failed attempts
            user.login_attempts = (user.login_attempts or 0) + 1

            # Lock account if too many attempts
            if user.login_attempts >= self.MAX_LOGIN_ATTEMPTS:
                user.account_locked = True

            await user_db.update(user)

            # Log failed attempt
            await self._log_security_event(
                user_id=user.id,
                event_type="failed_login",
                details={"attempts": user.login_attempts, "account_locked": user.account_locked}
            )

            return None

        # Successful login
        user.login_attempts = 0
        user.account_locked = False
        user.last_login_ip = None  # Will be set by middleware
        await user_db.update(user)

        # Log successful login
        await self._log_security_event(
            user_id=user.id,
            event_type="successful_login",
            details={"mfa_enabled": user.mfa_enabled}
        )

        return user

    async def _log_security_event(
        self,
        user_id: Optional[str] = None,
        event_type: str = "security_event",
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """Log security events for PSD-12 compliance"""
        try:
            session = await get_async_session()

            # Create audit trail entry
            audit_entry = AuditTrail(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                user_id=user_id,
                action=event_type,
                ip_address=ip_address,
                user_agent=user_agent,
                previous_values=None,
                new_values=details or {},
                psd_sections=["PSD-12"] if event_type in ["failed_login", "account_lockout_attempt"] else None,
                created_at=datetime.utcnow()
            )

            session.add(audit_entry)
            await session.commit()

        except Exception as e:
            print(f"Failed to log security event: {e}")
            # Don't fail the main operation if audit logging fails


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl=f"{AUTH_URL_PATH}/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.ACCESS_SECRET_KEY,
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
