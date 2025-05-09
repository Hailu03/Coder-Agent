"""API routes for application settings.

This module defines the API routes for updating and retrieving application settings.
"""

from fastapi import APIRouter, Body, HTTPException, Depends, Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel
from typing import Optional, Callable, Any
import os
import logging
import json
from dotenv import load_dotenv, set_key
from pathlib import Path
from ...core.config import settings, ROOT_DIR, reload_settings
from ...auth.deps import get_current_active_user
from ...db.models import User

# Configure logging
logger = logging.getLogger("api.settings")

# Create router 
router = APIRouter()

# ENV file path
ENV_FILE = os.path.join(ROOT_DIR, ".env")

# Request models
class SettingsUpdateRequest(BaseModel):
    """Model for settings update requests."""
    ai_provider: Optional[str] = None
    api_key: Optional[str] = None
    serper_api_key: Optional[str] = None

@router.post("/", response_model=dict)
async def update_settings(
    request: Request, 
    data: SettingsUpdateRequest = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """Update application settings.
    
    Args:
        request: The HTTP request
        data: The settings update request
        current_user: The authenticated user (must be active)
    
    Returns:
        Success status and message
    """
    try:
        logger.info(f"User {current_user.username} is updating application settings")
        logger.info(f"Request headers: {request.headers}")
        logger.info(f"Request body (settings to update): {data}")
        
        # Ensure .env file exists
        env_path = Path(ENV_FILE)
        logger.info(f"ENV file path: {env_path}, exists: {env_path.exists()}")
        
        if not env_path.exists():
            logger.warning(f"ENV file does not exist, creating at: {env_path}")
            with open(env_path, 'w') as f:
                f.write("# Application Settings\n")
        
        # Load current env content
        try:
            with open(env_path, 'r') as f:
                env_content = f.read()
            logger.info(f"Current .env content exists with {len(env_content)} characters")
        except Exception as e:
            logger.error(f"Error reading .env file: {str(e)}")
            env_content = "# Application Settings\n"
        
        # Function to update .env file directly
        def update_env_var(key, value):
            nonlocal env_content
            import re
            # Check if key exists
            pattern = rf'^{key}=.*$'
            if re.search(pattern, env_content, re.MULTILINE):
                # Update existing key
                logger.info(f"Updating existing key: {key}")
                env_content = re.sub(pattern, f'{key}={value}', env_content, flags=re.MULTILINE)
            else:
                # Add new key
                logger.info(f"Adding new key: {key}")
                env_content += f'\n{key}={value}'
        
        # Update settings based on request
        changes_made = False
        
        if data.ai_provider:
            if data.ai_provider not in ["gemini", "openai"]:
                logger.error(f"Invalid AI provider: {data.ai_provider}")
                raise HTTPException(status_code=400, detail="Invalid AI provider. Must be 'gemini' or 'openai'")
            
            logger.info(f"Setting AI_PROVIDER to {data.ai_provider}")
            update_env_var("AI_PROVIDER", data.ai_provider)
            os.environ["AI_PROVIDER"] = data.ai_provider
            changes_made = True
        
        if data.api_key:
            # Set the appropriate API key based on provider
            if data.ai_provider == "openai" or (not data.ai_provider and settings.AI_PROVIDER == "openai"):
                logger.info("Setting OPENAI_API_KEY")
                update_env_var("OPENAI_API_KEY", data.api_key)
                os.environ["OPENAI_API_KEY"] = data.api_key
            else:  # Default to Gemini
                logger.info("Setting GEMINI_API_KEY")
                update_env_var("GEMINI_API_KEY", data.api_key)
                os.environ["GEMINI_API_KEY"] = data.api_key
            
            changes_made = True
        
        if data.serper_api_key:
            logger.info("Setting SERPER_API_KEY")
            update_env_var("SERPER_API_KEY", data.serper_api_key)
            os.environ["SERPER_API_KEY"] = data.serper_api_key
            changes_made = True
        
        if not changes_made:
            logger.info("No changes were made to settings")
            return {"success": True, "message": "No changes were made to settings"}
        
        # Write back to .env file
        try:
            with open(env_path, 'w') as f:
                f.write(env_content)
            logger.info(f"Updated .env file successfully with {len(env_content)} characters")
        except Exception as e:
            logger.error(f"Error writing to .env file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to write to .env file: {str(e)}"
            )
        
        # Reload settings in application
        reload_settings()
        
        logger.info("Settings updated successfully")
        return {
            "success": True,
            "message": "Settings updated successfully. Please restart the server for changes to take effect."
        }
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update settings: {str(e)}"
        )


@router.get("/", response_model=dict)
async def get_settings(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get current application settings.
    
    Args:
        request: The HTTP request
        current_user: The authenticated user (must be active)
    
    Returns:
        Current settings
    """
    try:
        logger.info(f"User {current_user.username} is retrieving current settings")
        logger.info(f"Request headers: {request.headers}")
        
        # Don't return actual API keys, just indicate if they're set
        return {
            "ai_provider": settings.AI_PROVIDER,
            "gemini_api_key_set": bool(settings.GEMINI_API_KEY),
            "openai_api_key_set": bool(settings.OPENAI_API_KEY),
            "serper_api_key_set": bool(settings.SERPER_API_KEY)
        }
    except Exception as e:
        logger.error(f"Error retrieving settings: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve settings: {str(e)}"
        )