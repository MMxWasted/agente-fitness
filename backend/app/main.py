from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.readiness import router as readiness_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Authorization", "Content-Type"],
)
app.include_router(health_router)
app.include_router(readiness_router)
app.include_router(auth_router)
app.include_router(users_router)
