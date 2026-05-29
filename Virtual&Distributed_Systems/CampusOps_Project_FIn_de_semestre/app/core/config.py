from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    API_BASE_URL: str = "http://localhost:8000"

    # OpenClaw — shared secret for the external orchestrator
    OPENCLAW_KEY: str = ""

    # Mail (IMAP + SMTP)
    MAIL_HOST: str = ""
    MAIL_PORT_IMAP: int = 993
    MAIL_PORT_SMTP: int = 587
    MAIL_USER: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM_NAME: str = "CampusOps"
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"   # ← silently skip unknown vars like CAMPUSOPS_API_URL


settings = Settings()
