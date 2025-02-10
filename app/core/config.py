"""Configuration settings for the RAG Chatbot application.

This module defines the application settings using Pydantic BaseSettings.
It handles configuration for:
- Database connections
- Vector store settings
- LLM configuration
- Security settings
- Logging configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings and configuration.
    
    Attributes:
        PROJECT_NAME: Name of the project
        VERSION: Current version of the application
        API_V1_STR: API version prefix for all endpoints
        
        # Database Settings
        POSTGRES_SERVER: PostgreSQL server hostname
        POSTGRES_USER: Database username
        POSTGRES_PASSWORD: Database password
        POSTGRES_DB: Database name
        POSTGRES_PORT: Database port
        
        # Vector Store Settings
        QDRANT_HOST: Vector store server hostname
        QDRANT_PORT: Vector store server port
        VECTOR_DIMENSION: Dimension of embeddings
        
        # Redis Settings
        REDIS_HOST: Redis server hostname
        REDIS_PORT: Redis server port
        
        # LLM Settings
        LLM_API_KEY: API key for the language model service
        LLM_MODEL_NAME: Name of the language model to use
        LLM_MAX_TOKENS: Maximum tokens per response
        LLM_TEMPERATURE: Temperature for response generation
        LLM_PRESENCE_PENALTY: Penalty for token presence
        LLM_FREQUENCY_PENALTY: Penalty for token frequency
        LLM_CONTEXT_WINDOW: Maximum context window size
        LLM_MAX_RETRIES: Maximum retries for API calls
        LLM_TIMEOUT: Timeout for API calls in seconds
        
        # Security Settings
        SECRET_KEY: Secret key for JWT token generation
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time
        
        # Logging Settings
        LOG_LEVEL: Logging level (INFO, DEBUG, etc.)
        LOG_FORMAT: Log format (JSON or text)
        LOG_FILE: Path to log file
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
    VECTOR_DIMENSION: int = 768  # Dimension of embeddings
    
    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # LLM settings
    LLM_API_KEY: str = 'key'
    LLM_MODEL_NAME: str = "gpt-3.5-turbo"
    LLM_MAX_TOKENS: int = 1000
    LLM_TEMPERATURE: float = 0.7
    LLM_PRESENCE_PENALTY: float = 0.0
    LLM_FREQUENCY_PENALTY: float = 0.0
    LLM_CONTEXT_WINDOW: int = 4096
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT: int = 30
    LLM_SYSTEM_PROMPT: str = """You are a helpful AI assistant that answers questions based on the provided context.
If the answer cannot be found in the context, say "I don't have enough information to answer that."
Always be clear, concise, and accurate."""
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    LOG_JSON_FORMAT: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_RETENTION_DAYS: int = 30
    
    class Config:
        """Pydantic configuration class."""
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings() 
