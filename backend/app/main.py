from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.auth.router import router as auth_router
from app.bottle.router import router as bottle_router
from app.community.admin_router import router as community_admin_router
from app.community.router import router as community_router
from app.config import settings
from app.diary.router import router as diary_router
from app.discoveries.router import router as discoveries_router
from app.home.router import router as home_router
from app.learning.router import router as learning_router
from app.my_path.router import router as my_path_router
from app.onboarding.router import router as onboarding_router
from app.progress.router import router as progress_router
from app.shared.errors import AppError
from app.shared.responses import app_error_handler
from app.taste_profile.router import router as taste_profile_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_exception_handler(AppError, app_error_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix=settings.api_v1_prefix)
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(onboarding_router, prefix=settings.api_v1_prefix)
    app.include_router(discoveries_router, prefix=settings.api_v1_prefix)
    app.include_router(learning_router, prefix=settings.api_v1_prefix)
    app.include_router(progress_router, prefix=settings.api_v1_prefix)
    app.include_router(bottle_router, prefix=settings.api_v1_prefix)
    app.include_router(community_router, prefix=settings.api_v1_prefix)
    app.include_router(community_admin_router, prefix=settings.api_v1_prefix)
    app.include_router(diary_router, prefix=settings.api_v1_prefix)
    app.include_router(taste_profile_router, prefix=settings.api_v1_prefix)
    app.include_router(my_path_router, prefix=settings.api_v1_prefix)
    app.include_router(home_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
