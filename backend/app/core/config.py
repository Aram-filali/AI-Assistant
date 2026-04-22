from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    # Application
    APP_NAME: str = "AI Sales Assistant"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str | None = None
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    
    # === OpenRouter Config (au lieu d'OpenAI) ===
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"  # Ou "anthropic/claude-3-sonnet"
    
    # === RAG Settings ===
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"  # Free, local
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    DEFAULT_PUBLIC_KB_ID: str | None = None  # Default KB for public chat (if not provided)
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    
    # Email
    RESEND_API_KEY: str | None = None
    FROM_EMAIL: str | None = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 1
    
    # CRM Integrations
    # HubSpot
    HUBSPOT_API_KEY: str = ""
    HUBSPOT_CONTACT_LIST_ID: str = ""
    
    # Salesforce
    SALESFORCE_INSTANCE: str = ""  # e.g., "na1.salesforce.com" for US
    SALESFORCE_CLIENT_ID: str = ""
    SALESFORCE_CLIENT_SECRET: str = ""
    SALESFORCE_USERNAME: str = ""
    SALESFORCE_PASSWORD: str = ""
    SALESFORCE_SECURITY_TOKEN: str = ""
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Zoom
    ZOOM_CLIENT_ID: str = ""
    ZOOM_CLIENT_SECRET: str = ""
    ZOOM_ACCOUNT_ID: str = ""
    
    # CORS
    CORS_ORIGINS_STR: str = "http://localhost:3000"
    
    @field_validator('CORS_ORIGINS_STR', mode='after')
    @classmethod
    def validate_cors(cls, v):
        return v


settings = Settings()
