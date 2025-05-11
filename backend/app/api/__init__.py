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
from .v1 import auth as auth_router
from .v1 import events as events_router

# Include the solve routes
api_router.include_router(solve.router, prefix="/solve", tags=["solve"])

# Include the settings routes
api_router.include_router(settings_router.router, prefix="/settings", tags=["settings"])

# Include the authentication routes
api_router.include_router(auth_router.router, prefix="/auth", tags=["auth"])

# Include the events routes for real-time updates
api_router.include_router(events_router.router, prefix="/events", tags=["events"])