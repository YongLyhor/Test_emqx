from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

class DeviceTypeCreate(BaseModel):
    """Request schema for creating a device type"""
    type_code: str = Field(..., description="Unique type code", min_length=1, max_length=50)
    display_name: str = Field(..., description="Display name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Description")
    default_unit: str = Field(..., description="Default unit of measurement")
    min_value: Optional[float] = Field(None, description="Minimum expected value")
    max_value: Optional[float] = Field(None, description="Maximum expected value")
    alert_threshold: Optional[float] = Field(None, description="Alert threshold value")
    is_active: Optional[bool] = Field(True, description="Is this type active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type_code": "water",
                "display_name": "Water Meter",
                "description": "Measures water consumption in cubic meters",
                "default_unit": "m³",
                "min_value": 0,
                "max_value": 999999.999999,
                "alert_threshold": 5000,
                "is_active": True
            }
        }

class DeviceTypeUpdate(BaseModel):
    """Request schema for updating a device type"""
    display_name: Optional[str] = Field(None, description="Display name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Description")
    default_unit: Optional[str] = Field(None, description="Default unit of measurement")
    min_value: Optional[float] = Field(None, description="Minimum expected value")
    max_value: Optional[float] = Field(None, description="Maximum expected value")
    alert_threshold: Optional[float] = Field(None, description="Alert threshold value")
    is_active: Optional[bool] = Field(None, description="Is this type active")