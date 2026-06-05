from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Gravity-Matrix Backend"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/gravity_matrix.db"
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    llm_provider: str = "openai_compatible"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 120

    llm_fallback_provider: str = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b"

    min_chapters: int = Field(default=3, ge=1)
    max_chapters: int = Field(default=30, ge=1)
    max_chapter_chars: int = Field(default=20000, ge=100)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
