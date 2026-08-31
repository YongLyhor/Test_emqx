from fastapi import APIRouter, Depends
from datetime import datetime
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from sqlalchemy.orm import Session
from sqlalchemy import text

router = APIRouter(tags=["Health"])

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IoT Platform API",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    # Check database
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "version": settings.API_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "environment": settings.ENVIRONMENT
    }

@router.get("/health/readiness")
async def readiness_check():
    """Readiness probe for Kubernetes"""
    return {"status": "ready"}

@router.get("/health/liveness")
async def liveness_check():
    """Liveness probe for Kubernetes"""
    return {"status": "alive"}