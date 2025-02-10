"""Logging configuration for the RAG Chatbot.

This module provides a centralized logging configuration with:
- Console and file handlers
- JSON formatting for structured logging
- Different log levels for different environments
- Request ID tracking
- Rotation and backup management
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
from app.core.config import settings

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add module and function
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        
        # Add environment
        log_record['environment'] = settings.ENVIRONMENT
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id

def setup_logging() -> logging.Logger:
    """Configure and return the root logger."""
    
    # Create logger
    logger = logging.getLogger("rag-chatbot")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handlers
    # Main log file
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Error log file
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/error.log',
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    
    # Create JSON formatter
    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(module)s %(function)s %(message)s'
    )
    
    # Set formatters
    console_handler.setFormatter(json_formatter)
    file_handler.setFormatter(json_formatter)
    error_handler.setFormatter(json_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

# Create logger instance
logger = setup_logging() 