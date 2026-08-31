from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DeviceTypeResponse(BaseModel):
    """Response schema for device type (basic)"""
    id: int = Field(..., description="Type ID")
    type_code: str = Field(..., description="Type code")
    display_name: str = Field(..., description="Display name")
    default_unit: str = Field(..., description="Default unit")
    is_active: bool = Field(..., description="Is active")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "type_code": "water",
                "display_name": "Water Meter",
                "default_unit": "m³",
                "is_active": True
            }
        }

class DeviceTypeDetailResponse(DeviceTypeResponse):
    """Detailed response schema for device type"""
    description: Optional[str] = Field(None, description="Description")
    min_value: Optional[float] = Field(None, description="Minimum expected value")
    max_value: Optional[float] = Field(None, description="Maximum expected value")
    alert_threshold: Optional[float] = Field(None, description="Alert threshold")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "type_code": "water",
                "display_name": "Water Meter",
                "description": "Measures water consumption in cubic meters",
                "default_unit": "m³",
                "min_value": 0,
                "max_value": 999999.999999,
                "alert_threshold": 5000,
                "is_active": True,
                "created_at": "2026-08-27T00:00:00Z"
            }
        }