from typing import Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAPI docs
    OPENAPI_URL: str = "/openapi.json"

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    EXPIRE_ON_COMMIT: bool = False

    # User & Security (PSD-12 compliance)
    ACCESS_SECRET_KEY: str
    RESET_PASSWORD_SECRET_KEY: str
    VERIFICATION_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600

    # PSD-12 Cybersecurity compliance
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    PASSWORD_COMPLEXITY_MIN_LENGTH: int = 12
    MFA_REQUIRED: bool = True

    # Email
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_SERVER: str | None = None
    MAIL_PORT: int | None = None
    MAIL_FROM_NAME: str = "NAMFISA Regulatory Sandbox"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    TEMPLATE_DIR: str = "email_templates"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # External Services (BoN Integration)
    BON_API_URL: str = "https://api.bon.gov.na"
    BON_API_KEY: str | None = None
    BON_NOTIFICATION_EMAIL: str = "compliance@namfisa.com.na"

    # AI/ML Services
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-3-sonnet"

    # Vector Database (pgvector)
    VECTOR_DB_URL: str | None = None

    # Knowledge Graph (Neo4j)
    NEO4J_URI: str = "neo4j://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str

    # Caching
    REDIS_URL: str = "redis://localhost:6379/0"

    # File Storage
    S3_BUCKET_NAME: str = "namfisa-documents"
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None

    # Monitoring
    SENTRY_DSN: str | None = None
    DATADOG_API_KEY: str | None = None

    # CORS
    CORS_ORIGINS: Set[str] = {
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003",
        "http://localhost:8004",
        "http://localhost:8005",
        "http://localhost:8006",
        "http://localhost:8007"
    }

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
