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

    smtp_enabled: bool = False
    smtp_host: str = "smtp.mail.ovh.net"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "courriers@ibi.ci"
    notify_emails: str = ""
    backup_dir: str = "/data/backups"
    ocr_enabled: bool = True
    migration_dir: str = "/data/migration"
    cookie_name: str = "ibi_session"
    cookie_secure: bool | None = None
    rate_limit_ocr_max: int = 8
    rate_limit_ocr_window_sec: int = 300

    @property
    def notify_emails_list(self) -> list[str]:
        return [e.strip() for e in self.notify_emails.split(",") if e.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
