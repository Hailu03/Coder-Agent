from fastapi import Depends, HTTPException, status, Request as FastAPIRequest
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import fastapi
from jose import jwt
import logging

from ..db.database import get_db
from ..db.models import User
from .utils import decode_token
from typing import Optional

# Configure logging
logger = logging.getLogger("auth.deps")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

async def get_current_user(
    request: FastAPIRequest = None,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from token.
    For SSE connections, also check query parameters since EventSource can't set headers.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
      # First try the standard OAuth2 token from header
    if not token and request:
        # If no token in header, check query parameters (for EventSource)
        token = request.query_params.get("token")
        logger.info(f"Using token from query params: {token[:10]}..." if token else "No token in query params")
    else:
        logger.info(f"Using token from header: {token[:10]}..." if token else "No token in header")
    
    if not token:
        raise credentials_exception
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    # Check if token is an access token (not a refresh token)
    token_type = payload.get("token_type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
            
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
        
    return user

async def get_user_from_token_param(token: str, db: Session = Depends(get_db)) -> User:
    """
    Get user from token provided as query parameter
    This is used for EventSource connections which can't set Authorization headers
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        logger.error("Missing token in query parameter")
        raise credentials_exception
        
    logger.info(f"Authenticating with token from query param: {token[:10]}...")
    
    payload = decode_token(token)
    if payload is None:
        logger.error("Invalid token in query parameter")
        raise credentials_exception
        
    # Check if token is an access token (not a refresh token)
    token_type = payload.get("token_type")
    if token_type != "access":
        logger.error(f"Invalid token type in query parameter: {token_type}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    username: str = payload.get("sub")
    if username is None:
        logger.error("No username in token payload")
        raise credentials_exception
            
    user = db.query(User).filter(User.username == username).first()
    
    if user is None:
        logger.error(f"No user found for username: {username}")
        raise credentials_exception
        
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return current_user