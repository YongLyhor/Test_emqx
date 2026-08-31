from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.core.logging import logger

# Security (optional - for future JWT implementation)
security = HTTPBearer(auto_error=False)

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Get current user from JWT token (optional)"""
    if not credentials:
        return None
    
    # TODO: Implement JWT validation
    # For now, just return the token
    return credentials.credentials

def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Require authentication"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

def get_pagination_params(
    limit: int = 100,
    offset: int = 0
) -> dict:
    """Get pagination parameters"""
    return {"limit": min(limit, 1000), "offset": max(offset, 0)}