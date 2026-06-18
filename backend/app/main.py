from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.novel_scripts import router as novel_scripts_router
from app.api.routes.parse import router as parse_router
from app.api.routes.projects import router as projects_router
from app.core.config import settings
from app.db.init_db import init_db


def create_app() -> FastAPI:
    _print_llm_startup_config()
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


def _print_llm_startup_config() -> None:
    print(f"LLM_PROVIDER={settings.llm_provider}", flush=True)
    print(f"LLM_BASE_URL={settings.llm_base_url}", flush=True)
    print(f"LLM_MODEL={settings.llm_model}", flush=True)
    print(f"LLM_TIMEOUT_SECONDS={settings.llm_timeout_seconds}", flush=True)
    print(f"LLM_API_KEY_SET={str(bool(settings.llm_api_key)).lower()}", flush=True)


def _validate_llm_startup_config() -> None:
    base_url = (settings.llm_base_url or "").strip()
    if not base_url:
        print("LLM_BASE_URL is empty; AI endpoints will require LLM config.", flush=True)
        return
    if not base_url.startswith(("http://", "https://")):
        raise RuntimeError(
            "LLM_BASE_URL 必须以 http:// 或 https:// 开头，"
            f"当前值为：{settings.llm_base_url!r}"
        )


app = create_app()
