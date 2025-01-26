from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings configuration"""
    

    DATABASE_URL: str
    JWT_SECRET_KEY: str

    # SMTP settings
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    REDIS_URL: str
    
    # Email Template Settings
    EMAIL_SENDER_NAME: str = "Health Haven"
    PASSWORD_RESET_TIMEOUT: int = 3600  # 1 hour in seconds
    
    class Config:
        env_file = "backend/env/.env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Create cached settings instance"""
    return Settings()

# Export settings instance
settings = get_settings()