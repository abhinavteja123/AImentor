"""
Configuration settings for AI Life Mentor Backend
Uses Pydantic Settings for environment variable management
"""

from functools import lru_cache
from typing import List, Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""
    
    # App Settings
    APP_NAME: str = "AI Life Mentor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins and strip trailing slashes."""
        origins = [origin.strip().rstrip('/') for origin in self.CORS_ORIGINS.split(",")]
        # Filter out empty strings
        return [origin for origin in origins if origin]
    
    # LLM providers — primary + fallback chain
    LLM_PROVIDER: str = "groq"  # groq | cerebras | gemini
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    CEREBRAS_API_KEY: str = ""
    CEREBRAS_MODEL: str = "llama3.1-8b"
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Feature flags
    USE_LLM_CURRICULUM: bool = True  # When True, roadmap curriculum is LLM-generated with hardcoded fallback

    # Research-harness seams (default-off so production behaviour is unchanged).
    USE_SEMANTIC_ATS: bool = False
    INTENT_STRATEGY: Literal["rule", "fewshot", "learned"] = "rule"
    INTENT_CHECKPOINT_PATH: str = ""
    
    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aimentor"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "your_super_secret_jwt_key_change_this_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields like NEXT_PUBLIC_API_URL


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
