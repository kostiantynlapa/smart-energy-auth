"""
Configuration management using environment variables.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    class Config:
        env_file = str(Path(__file__).parent / ".env")
        case_sensitive = True


settings = Settings()
