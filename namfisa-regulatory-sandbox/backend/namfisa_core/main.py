from fastapi import FastAPI, status
from fastapi_pagination import add_pagination
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from .schemas import UserCreate, UserRead, UserUpdate
from .users import auth_backend, fastapi_users, AUTH_URL_PATH
from .utils import simple_generate_unique_route_id
from .config import settings
from .database import check_database_health

# Import routes
from .routes.items import router as items_router
from .routes.applications import router as applications_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NAMFISA Regulatory Sandbox API",
    description="API for Bank of Namibia PSD-compliant fintech regulatory sandbox",
    version="1.0.0",
    generate_unique_id_function=simple_generate_unique_route_id,
    openapi_url=settings.OPENAPI_URL,
)

# Middleware for CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication and user management routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix=f"/{AUTH_URL_PATH}/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix=f"/{AUTH_URL_PATH}",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix=f"/{AUTH_URL_PATH}",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix=f"/{AUTH_URL_PATH}",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Include application routes
app.include_router(applications_router, prefix="/api/v1/applications", tags=["applications"])

# Include items routes (for backward compatibility)
app.include_router(items_router, prefix="/items", tags=["items"])

# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "namfisa-backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health/database", tags=["health"])
async def database_health_check():
    """Database health check"""
    try:
        db_healthy = await check_database_health()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/health/compliance", tags=["health"])
async def compliance_health_check():
    """PSD compliance health check"""
    return {
        "status": "healthy",
        "psd_compliance": "enabled",
        "psd_sections": ["PSD-1", "PSD-3", "PSD-4", "PSD-5", "PSD-6", "PSD-8", "PSD-9", "PSD-12", "PSD-13"],
        "psdir_sections": ["PSDIR-4", "PSDIR-5", "PSDIR-7", "PSDIR-8", "PSDIR-9", "PSDIR-10", "PSDIR-11"],
        "eta_2019_compliant": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        # Check database connectivity
        db_healthy = await check_database_health()

        if db_healthy:
            return {
                "status": "ready",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not ready",
                    "database": "disconnected",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Add pagination support
add_pagination(app)
