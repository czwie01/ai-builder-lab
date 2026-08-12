"""Application settings, loaded from the environment with the RAG_API_ prefix."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_API_")

    app_name: str = "ai-builder-lab RAG API"
    log_level: str = "INFO"
    guard_max_question_length: int = 1000
