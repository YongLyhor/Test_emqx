import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
import threading

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.logging import logger, get_logger
from app.core.exceptions import (
    BaseAppException,
    DeviceNotFoundError,
    DeviceAlreadyExistsError,
    InvalidSensorTypeError,
    ValidationError,
    DatabaseError,
    RecordNotFoundError,
    to_http_exception
)

# Import routers
from app.api.routes import health, sensors, devices, alerts, device_types

# Global MQTT initializer
mqtt_initializer = None

# =============================================
# Lifespan Manager
# =============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup and shutdown events"""
    global mqtt_initializer
    
    # ----- STARTUP -----
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {app.title} v{app.version}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    logger.info("=" * 60)
    
    # Initialize database (create tables if not exist)
    try:
        from app.models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified/created")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
    
    # Initialize MQTT in background thread (non-blocking)
    if settings.ENVIRONMENT != "testing":
        def init_mqtt():
            global mqtt_initializer
            try:
                from app.mqtt.initializer import MQTTInitializer
                db = SessionLocal()
                try:
                    mqtt_initializer = MQTTInitializer(db)
                    if mqtt_initializer.initialize():
                        logger.info("✅ MQTT initialized successfully")
                    else:
                        logger.warning("⚠️ MQTT initialization failed - continuing without MQTT")
                finally:
                    db.close()
            except ImportError as e:
                logger.warning(f"⚠️ MQTT module not available: {e}")
            except Exception as e:
                logger.error(f"❌ Error initializing MQTT: {e}")
        
        # Start MQTT in background thread with timeout
        mqtt_thread = threading.Thread(target=init_mqtt, daemon=True)
        mqtt_thread.start()
        logger.info("🔄 MQTT initialization started in background...")
    
    # Log API documentation URLs
    logger.info("📚 API Documentation:")
    logger.info(f"   Swagger UI: http://localhost:{settings.API_PORT}/docs")
    logger.info(f"   ReDoc:     http://localhost:{settings.API_PORT}/redoc")
    
    yield  # Application runs here
    
    # ----- SHUTDOWN -----
    logger.info("=" * 60)
    logger.info("🛑 Shutting down application...")
    
    # Shutdown MQTT
    if mqtt_initializer:
        try:
            mqtt_initializer.shutdown()
            logger.info("✅ MQTT shutdown complete")
        except Exception as e:
            logger.error(f"❌ Error shutting down MQTT: {e}")
    
    # Close database connections
    try:
        engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")
    
    logger.info("👋 Application shutdown complete")
    logger.info("=" * 60)


# =============================================
# Create FastAPI Application
# =============================================

app = FastAPI(
    title="IoT Platform API",
    description="""
    ## IoT Platform API
    
    A production-ready API for managing IoT sensor data with:
    - **EMQX** for MQTT communication
    - **TimescaleDB** for time-series data storage
    - **Real-time** data processing and alerts
    - **Anomaly detection** using Z-score analysis
    - **Automatic aggregation** for performance
    
    ### Features
    - 📊 Sensor data ingestion and storage
    - 🔔 Alert management with thresholds
    - 📈 Time-series aggregation
    - 🔍 Anomaly detection
    - 📱 Device management
    - 🔐 Secure (JWT ready)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    contact={
        "name": "IoT Platform Team",
        "email": "support@iot-platform.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)


# =============================================
# Middleware
# =============================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if hasattr(settings, 'ALLOWED_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    request_id = request.headers.get("X-Request-ID", f"{datetime.utcnow().timestamp():.0f}")
    
    # Log request
    logger.info(f"🔵 {request.method} {request.url.path} [Request-ID: {request_id}]")
    
    # Process request
    start_time = datetime.utcnow()
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)}")
        raise
    
    # Log response
    duration = (datetime.utcnow() - start_time).total_seconds() * 1000
    status_symbol = "✅" if response.status_code < 400 else "❌" if response.status_code >= 500 else "⚠️"
    logger.info(f"{status_symbol} {request.method} {request.url.path} - {response.status_code} [{duration:.0f}ms]")
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.0f}ms"
    
    return response


# =============================================
# Exception Handlers
# =============================================

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handle custom application exceptions"""
    logger.error(f"Application exception: {exc.message} (Status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.detail} (Status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "details": str(exc) if settings.ENVIRONMENT != "production" else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# =============================================
# Include Routers
# =============================================

app.include_router(health.router)
app.include_router(sensors.router)
app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(device_types.router)


# =============================================
# Root Endpoint
# =============================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "IoT Platform API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs" if settings.ENVIRONMENT != "production" else None,
        "status": "operational"
    }


# =============================================
# Health Check (Enhanced)
# =============================================

@app.get("/health", tags=["Root"])
async def health_check():
    """Comprehensive health check"""
    global mqtt_initializer
    
    # Check database
    db_status = "disconnected"
    try:
        from sqlalchemy import text
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {e}")
    
    # Check MQTT
    mqtt_status = "disconnected"
    if mqtt_initializer and mqtt_initializer.client:
        mqtt_status = "connected" if mqtt_initializer.client.is_connected() else "disconnected"
    
    # Determine overall status
    overall_status = "healthy" if db_status == "connected" else "unhealthy"
    
    return {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": {
                "status": db_status,
                "name": "TimescaleDB"
            },
            "mqtt": {
                "status": mqtt_status,
                "broker": settings.MQTT_BROKER_HOST
            },
            "api": {
                "status": "healthy",
                "environment": settings.ENVIRONMENT
            }
        }
    }


# =============================================
# Application Metadata Endpoints
# =============================================

@app.get("/info", tags=["Root"])
async def get_info():
    """Get application information"""
    return {
        "name": "IoT Platform API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "features": {
            "mqtt": True,
            "timescaledb": True,
            "alerts": True,
            "aggregations": True,
            "anomaly_detection": True
        },
        "dependencies": {
            "fastapi": "0.104.1",
            "sqlalchemy": "2.0.23",
            "timescaledb": "latest",
            "emqx": "latest"
        },
        "endpoints": {
            "total": len(app.routes),
            "api_prefixes": ["/api/v1"],
            "documentation": "/docs"
        }
    }


# =============================================
# Shutdown Handler (Fallback)
# =============================================

@app.on_event("shutdown")
async def shutdown_event():
    """Additional shutdown cleanup"""
    global mqtt_initializer
    
    logger.info("🛑 Running shutdown cleanup...")
    
    if mqtt_initializer:
        try:
            mqtt_initializer.shutdown()
        except Exception as e:
            logger.error(f"Error during MQTT shutdown: {e}")
    
    try:
        engine.dispose()
    except Exception as e:
        logger.error(f"Error disposing engine: {e}")
    
    logger.info("✅ Shutdown cleanup complete")


# =============================================
# Main Entry Point (for running directly)
# =============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.ENVIRONMENT == "development"
    )