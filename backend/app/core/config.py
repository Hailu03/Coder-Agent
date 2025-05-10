"""Configuration settings for the Collaborative Coding Agents application.

This module defines the configuration settings for the application,
loading values from environment variables with sensible defaults.
"""

import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Optional, Union
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger("config")

# Determine the root directory of the application
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def parse_cors_origins(cors_origins: Union[str, List]) -> List[str]:
    """Parse CORS origins from string or list."""
    if isinstance(cors_origins, list):
        return cors_origins
    try:
        return json.loads(cors_origins)
    except (json.JSONDecodeError, TypeError):
        return [origin.strip() for origin in cors_origins.split(",")]


class Settings(BaseSettings):
    """Settings class for application configuration.
    
    Attributes are loaded from environment variables with defaults.
    """
    # Project name
    PROJECT_NAME: str = "Collaborative Coding Agents"
    PROJECT_DESCRIPTION: str = "Multi-agent AI system that transforms requirements into clean, optimized code"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    
    # CORS settings - use custom parser for string or list input
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:80", "http://localhost", "http://localhost:5173", "http://frontend:5173", "http://frontend:80"]
    
    # AI providers
    AI_PROVIDER: str = os.environ.get("AI_PROVIDER")  # Default to Gemini
    
    # Google Gemini settings
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY", None)
    OPENAI_MODEL: str = "gpt-4o-mini"

    
    # External API settings
    SERPER_API_KEY: Optional[str] = None

    # MCP URL - supports different environments (local dev vs Docker)
    # Environment variable can override this default
    MCP_URL: str = os.environ.get("MCP_URL", "http://mcp-server:9000/sse")
    
    # Database settings
    SQL_DB_URL: Optional[str] = os.environ.get("SQL_DB_URL", "mysql+pymysql://root:123@mysql:3308/proagents")
    
    # Authentication settings
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "your_super_secret_key_for_jwt_tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Use less memory-intensive options when running in constrained environments
    # Set this to True if running in Docker containers with limited memory
    LOW_MEMORY_MODE: bool = os.environ.get("LOW_MEMORY_MODE", "").lower() == "true"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse and return CORS origins."""
        return parse_cors_origins(self.BACKEND_CORS_ORIGINS)

    class Config:
        """Configuration for settings."""
        env_file = os.path.join(ROOT_DIR, ".env")
        case_sensitive = True


# Create global settings object
settings = Settings()

# Function to reload settings after .env file changes
def reload_settings():
    """Reload settings from environment variables and .env file.
    
    This function is called when settings are updated through the API.
    It reloads environment variables from the .env file and 
    creates a new settings object with the updated values.
    """
    global settings
    try:
        # Reload environment from .env file
        env_path = os.path.join(ROOT_DIR, ".env")
        if os.path.exists(env_path):
            # Đọc file .env và cập nhật biến môi trường thủ công
            with open(env_path, "r") as f:
                env_file_content = f.read()
            
            # Phân tích từng dòng trong file .env
            for line in env_file_content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Cập nhật biến môi trường hiện tại
                    os.environ[key] = value
                    logger.info(f"Updated environment variable: {key}")
            
            logger.info(f"Reloaded environment variables from {env_path}")
        
        # Create a new settings object to pick up new values
        settings = Settings()
        
        # Log các thông tin cấu hình quan trọng
        logger.info(f"Settings reloaded successfully.")
        logger.info(f"AI Provider (from env): {os.environ.get('AI_PROVIDER')}")
        logger.info(f"AI Provider (from settings): {settings.AI_PROVIDER}")
        logger.info(f"OpenAI API key set: {bool(settings.OPENAI_API_KEY)}")
        logger.info(f"Gemini API key set: {bool(settings.GEMINI_API_KEY)}")
        
        return True
    except Exception as e:
        logger.error(f"Error reloading settings: {e}")
        return False

# Validate API keys
# if settings.AI_PROVIDER == "gemini" and not settings.GEMINI_API_KEY:
#     import warnings
#     warnings.warn(
#         "GEMINI_API_KEY not set in environment variables or .env file. "
#         "Set this variable to use the Gemini AI service."
#     )

# if settings.AI_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
#     import warnings
#     warnings.warn(
#         "OPENAI_API_KEY not set in environment variables or .env file. "
#         "Set this variable to use the OpenAI service."
#     )