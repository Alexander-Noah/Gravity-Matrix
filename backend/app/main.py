import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.novel_scripts import router as novel_scripts_router
from app.api.routes.parse import router as parse_router
from app.api.routes.projects import router as projects_router
from app.core.config import settings
from app.db.init_db import init_db

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    _log_llm_startup_config()
    _validate_llm_startup_config()

    app = FastAPI(title=settings.app_name)
    init_db()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(parse_router, prefix=settings.api_prefix)
    app.include_router(parse_router, prefix="/api")
    app.include_router(projects_router, prefix=settings.api_prefix)
    app.include_router(novel_scripts_router, prefix=settings.api_prefix)
    return app


def _log_llm_startup_config() -> None:
    logger.info("LLM_PROVIDER=%s", settings.llm_provider)
    logger.info("LLM_BASE_URL=%s", settings.llm_base_url)
    logger.info("LLM_MODEL=%s", settings.llm_model)
    logger.info("LLM_TIMEOUT_SECONDS=%s", settings.llm_timeout_seconds)
    logger.info("LLM_API_KEY_SET=%s", str(bool(settings.llm_api_key)).lower())


def _validate_llm_startup_config() -> None:
    base_url = (settings.llm_base_url or "").strip()
    if not base_url:
        logger.warning("LLM_BASE_URL is empty; AI endpoints will require LLM config.")
        return
    if not base_url.startswith(("http://", "https://")):
        raise RuntimeError(
            "LLM_BASE_URL 必须以 http:// 或 https:// 开头，"
            f"当前值为：{settings.llm_base_url!r}"
        )


app = create_app()
