from typing import AsyncGenerator
from urllib.parse import urlparse

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .models import Base, User


# Parse database URL for async connection
parsed_db_url = urlparse(settings.DATABASE_URL)

async_db_connection_url = (
    f"postgresql+asyncpg://{parsed_db_url.username}:{parsed_db_url.password}@"
    f"{parsed_db_url.hostname}{':' + str(parsed_db_url.port) if parsed_db_url.port else ''}"
    f"{parsed_db_url.path}"
)

# Create async engine with connection pooling for production
engine = create_async_engine(
    async_db_connection_url,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False
)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=settings.EXPIRE_ON_COMMIT
)


async def create_db_and_tables():
    """Create all database tables with proper error handling"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with proper error handling"""
    try:
        async with async_session_maker() as session:
            yield session
    except Exception as e:
        print(f"❌ Database session error: {e}")
        raise


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Get user database for FastAPI-Users"""
    yield SQLAlchemyUserDatabase(session, User)


# Health check function for database connectivity
async def check_database_health() -> bool:
    """Check database connectivity and health"""
    try:
        async with async_session_maker() as session:
            # Simple query to test connection
            result = await session.execute("SELECT 1 as health_check")
            return result.scalar() == 1
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False
