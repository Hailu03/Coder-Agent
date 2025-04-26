"""API router module for the Collaborative Coding Agents API.

This module defines the API routes for the application.
"""

from fastapi import APIRouter
from ..core.config import settings as config_settings

# Create API router
api_router = APIRouter()

# Include other routers here if the application grows
# For example: api_router.include_router(user_router, prefix="/users", tags=["users"])

# Import and include routes to avoid circular imports
from .v1 import solve
from .v1 import settings as settings_router

# Include the solve routes
api_router.include_router(solve.router, prefix="/solve", tags=["solve"])

# Include the settings routes
api_router.include_router(settings_router.router, prefix="/settings", tags=["settings"])