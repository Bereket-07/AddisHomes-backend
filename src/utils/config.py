import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Real Estate Platform Ethiopia"
    LOG_LEVEL: str = "INFO"
    
    # Firestore
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    SERVICE_URL: str = os.getenv("SERVICE_URL")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    ADMIN_TG_USERNAME: str = os.getenv("ADMIN_TG_USERNAME")  # Default to a placeholder if not set
    WEB_APP_URL: str = "https://realestate.et"
    
    # Admin
    ADMIN_PHONE_NUMBER: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    class Config:
        case_sensitive = True

settings = Settings()