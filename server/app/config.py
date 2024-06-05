from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://support:support@localhost:5432/support"
    secret_key: str
    access_token_expire_minutes: int = 60 * 12

    # Comma separated list, e.g. "http://localhost:5173,https://support.example.com"
    cors_origins: str = "http://localhost:5173"

    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_timeout_seconds: float = 30.0
    ai_requests_per_minute: int = 20

    max_upload_size_mb: int = 5
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
