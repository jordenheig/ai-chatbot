"""Configuration settings for the RAG Chatbot application.

This module defines the application settings using Pydantic BaseSettings.
It handles configuration for database, vector store, LLM, and security settings.

Environment variables can override these settings. For local development,
settings can be specified in a .env file.
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings and configuration.
    
    Attributes:
        PROJECT_NAME: Name of the project
        VERSION: Current version of the application
        API_V1_STR: API version prefix for all endpoints
        POSTGRES_SERVER: PostgreSQL server hostname
        POSTGRES_USER: Database username
        POSTGRES_PASSWORD: Database password
        POSTGRES_DB: Database name
        POSTGRES_PORT: Database port
        QDRANT_HOST: Vector store server hostname
        QDRANT_PORT: Vector store server port
        REDIS_HOST: Redis server hostname
        REDIS_PORT: Redis server port
        LLM_API_KEY: API key for the language model service
        LLM_MODEL_NAME: Name of the language model to use
        SECRET_KEY: Secret key for JWT token generation
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time in minutes
        LOG_LEVEL: Logging level
        ENVIRONMENT: Environment
        LOG_JSON_FORMAT: Whether to log in JSON format
        LOG_FILE_PATH: Path to the log file
        LOG_RETENTION_DAYS: Number of days to retain log files
        VECTOR_DIMENSION: Dimension of embeddings
        MAX_TOKENS: Maximum tokens for LLM
        TEMPERATURE: Temperature for LLM
    """
    
    PROJECT_NAME: str = "RAG Chatbot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "ragchatbot"
    POSTGRES_PORT: str = "5432"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Constructs the database URI from individual settings."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Vector DB settings
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    
    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # LLM settings
    LLM_API_KEY: str
    LLM_MODEL_NAME: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7
    
    # Security settings
    SECRET_KEY: str = 'security-key'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    LOG_JSON_FORMAT: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_RETENTION_DAYS: int = 30
    
    # Vector Store settings
    VECTOR_DIMENSION: int = 768  # Dimension of embeddings
    
    class Config:
        """Pydantic configuration class."""
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings() 
