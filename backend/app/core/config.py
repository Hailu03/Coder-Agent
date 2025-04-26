"""Configuration settings for the Collaborative Coding Agents application.

This module defines the configuration settings for the application,
loading values from environment variables with sensible defaults.
"""

import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import warnings

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
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:80", "http://frontend:80", "http://frontend:5173"]
    
    # AI providers
    AI_PROVIDER: str = "gemini"  # "gemini" or "openai"
    
    # Google Gemini settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash-lite"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4.1-nano"
    
    # External API settings
    SERPER_API_KEY: Optional[str] = None
    
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