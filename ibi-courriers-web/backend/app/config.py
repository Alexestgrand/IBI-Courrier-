"""Configuration de l'application (variables d'environnement)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://ibi:ibi_secret@localhost:5432/ibi_courriers"
    secret_key: str = "changez-moi-en-production"
    access_token_expire_minutes: int = 480
    upload_dir: str = "/data/uploads"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    environment: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
