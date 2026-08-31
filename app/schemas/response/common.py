from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset for pagination")
    has_more: bool = Field(..., description="Whether there are more items")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "limit": 50,
                "offset": 0,
                "has_more": True
            }
        }

class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = Field(False, description="Success flag")
    message: str = Field(..., description="Error message")
    details: Optional[Any] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Device not found",
                "details": {"device_id": "WTR-999"},
                "timestamp": "2026-08-27T10:00:00Z"
            }
        }

class SuccessResponse(BaseModel):
    """Success response schema"""
    success: bool = Field(True, description="Success flag")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Device created successfully",
                "data": {"device_id": "WTR-001"},
                "timestamp": "2026-08-27T10:00:00Z"
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Response timestamp")
    database: str = Field(..., description="Database status")
    mqtt: Optional[str] = Field(None, description="MQTT status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-08-27T10:00:00Z",
                "database": "connected",
                "mqtt": "connected"
            }
        }