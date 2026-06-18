from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "Gravity-Matrix Backend"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/gravity_matrix.db"
    frontend_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )

    llm_provider: str = "openai_compatible"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 120
    llm_max_concurrency: int = Field(default=2, ge=1)
    llm_max_retries: int = Field(default=0, ge=0)
    llm_chunk_size: int = Field(default=3500, ge=500)
    llm_chunk_overlap: int = Field(default=0, ge=0)
    llm_enable_cache: bool = True

    llm_fallback_provider: str = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b"

    min_chapters: int = Field(default=3, ge=1)
    max_chapters: int = Field(default=30, ge=1)
    max_chapter_chars: int = Field(default=20000, ge=100)
    max_script_yaml_chars: int = Field(default=1_000_000, ge=1000)

    jwt_secret_key: str = "gravity-matrix-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=1440, ge=1)

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
