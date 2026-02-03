import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Real Estate Platform Ethiopia"
    LOG_LEVEL: str = "INFO"
    
    # Database Configuration
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "mysql")  # "firestore" or "mysql"
    
    # MySQL Configuration (for cPanel compatibility)
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "real_estate_platform")
    
    # Firestore (legacy support)
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    SERVICE_URL: str = os.getenv("SERVICE_URL")
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    ADMIN_TG_USERNAME: str = os.getenv("ADMIN_TG_USERNAME")  # Default to a placeholder if not set
    WEB_APP_URL: str = os.getenv("WEB_APP_URL", "https://addishomess.com")
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    
    # Admin
    ADMIN_PHONE_NUMBER: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    class Config:
        case_sensitive = True

settings = Settings()