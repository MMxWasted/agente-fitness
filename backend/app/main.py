from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.body_measurement_imports import (
    router as body_measurement_imports_router,
)
from app.api.routes.body_measurement_reviews import (
    router as body_measurement_reviews_router,
)
from app.api.routes.body_measurement_sources import (
    router as body_measurement_sources_router,
)
from app.api.routes.health import router as health_router
from app.api.routes.profile import router as profile_router
from app.api.routes.readiness import router as readiness_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT"],
    allow_headers=["Accept", "Authorization", "Content-Type", "Idempotency-Key"],
)
app.include_router(health_router)
app.include_router(readiness_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profile_router)
app.include_router(body_measurement_sources_router)
app.include_router(body_measurement_imports_router)
app.include_router(body_measurement_reviews_router)
