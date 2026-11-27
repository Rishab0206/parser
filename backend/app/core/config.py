import os
import tempfile
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

DEFAULT_TEMP_STORAGE = os.path.join(tempfile.gettempdir(), "bsi_uploads")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bank Statement Intelligence Module"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./bank_intelligence.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    STORAGE_PATH: str = DEFAULT_TEMP_STORAGE
    
    # Encryption key: 32 bytes base64 encoded
    ENCRYPTION_KEY: str = "u2h_wXg-94xK8W_7D_K7Y1b6-M_d7s6y1A_z9L3m5_k="
    
    # JWT & Auth
    JWT_SECRET: str = "bank_intelligence_jwt_secret_change_in_prod_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    LOG_LEVEL: str = "INFO"
    PARSER_VERSION: str = "2.0.0"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
