"""FastAPI application factory with CORS, error handlers, and Mongo lifespan."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from smartcvapply.api.v1.router import api_router
from smartcvapply.api.v1.system import router as system_router
from smartcvapply.core.config import get_settings
from smartcvapply.core.db import close_mongo, create_mongo_client, init_beanie
from smartcvapply.core.exceptions import register_exception_handlers
from smartcvapply.core.logging import configure_logging, get_logger
from smartcvapply.core.storage import ObjectStorage
from smartcvapply.models import CV, FeedbackEvent, FillSession, LearnedMapping, Profile, User

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    configure_logging()
    s = get_settings()
    client = create_mongo_client()
    try:
        await init_beanie(
            client, db_name=s.mongo_db,
            document_models=[User, Profile, CV, LearnedMapping, FillSession, FeedbackEvent],
        )
    except Exception as e:
        log.warning("beanie_init_failed_continuing", error=str(e))
    if not s.fernet_key:
        log.error("fernet_key_not_set")
        raise RuntimeError("FERNET_KEY is not set — generate one and add it to .env")
    if s.app_env == "production" and s.jwt_secret in ("", "dev-secret-please-change-32+chars"):
        log.error("jwt_secret_not_set")
        raise RuntimeError("JWT_SECRET must be changed in production")
    storage = ObjectStorage()
    await storage.check_connection()
    log.info("app_started", env=s.app_env)
    yield
    await close_mongo(client)
    log.info("app_stopped")


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="SmartCVapply API",
        version="0.1.0",
        lifespan=lifespan,
    )
    if s.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=s.cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(system_router)
    return app


app = create_app()
