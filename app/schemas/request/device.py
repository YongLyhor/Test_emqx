from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import date

class DeviceCreate(BaseModel):
    """Request schema for creating a new device"""
    device_id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Device display name", min_length=1, max_length=200)
    sensor_type: str = Field(..., description="Type of sensor: water, electricity, gas, cooling")
    location: Optional[str] = Field(None, description="Device location")
    building: Optional[str] = Field(None, description="Building name")
    floor: Optional[int] = Field(None, description="Floor number", ge=-10, le=100)
    room: Optional[str] = Field(None, description="Room identifier")
    installation_date: Optional[date] = Field(None, description="Installation date")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    status: Optional[str] = Field('active', description="Device status: active, inactive, maintenance")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional device metadata")
    
    @validator('sensor_type')
    def validate_sensor_type(cls, v):
        allowed_types = ['water', 'electricity', 'gas', 'cooling']
        if v.lower() not in allowed_types:
            raise ValueError(f'sensor_type must be one of: {allowed_types}')
        return v.lower()
    
    @validator('status')
    def validate_status(cls, v):
        allowed_status = ['active', 'inactive', 'maintenance']
        if v and v.lower() not in allowed_status:
            raise ValueError(f'status must be one of: {allowed_status}')
        return v.lower() if v else 'active'
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "WTR-001-BLDG-A",
                "name": "Main Water Meter - Building A",
                "sensor_type": "water",
                "location": "Basement - Utility Room 101",
                "building": "Building A",
                "floor": -1,
                "room": "Utility Room 101",
                "installation_date": "2025-06-15",
                "firmware_version": "v2.3.1",
                "status": "active",
                "metadata": {
                    "manufacturer": "Siemens",
                    "model": "Sitrans F M230"
                }
            }
        }

class DeviceUpdate(BaseModel):
    """Request schema for updating an existing device"""
    name: Optional[str] = Field(None, description="Device display name", min_length=1, max_length=200)
    location: Optional[str] = Field(None, description="Device location")
    building: Optional[str] = Field(None, description="Building name")
    floor: Optional[int] = Field(None, description="Floor number", ge=-10, le=100)
    room: Optional[str] = Field(None, description="Room identifier")
    installation_date: Optional[date] = Field(None, description="Installation date")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    status: Optional[str] = Field(None, description="Device status: active, inactive, maintenance")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional device metadata")
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_status = ['active', 'inactive', 'maintenance']
            if v.lower() not in allowed_status:
                raise ValueError(f'status must be one of: {allowed_status}')
            return v.lower()
        return v

class DeviceQueryParams(BaseModel):
    """Query parameters for filtering devices"""
    sensor_type: Optional[str] = Field(None, description="Filter by sensor type")
    status: Optional[str] = Field(None, description="Filter by status")
    building: Optional[str] = Field(None, description="Filter by building")
    location: Optional[str] = Field(None, description="Filter by location")
    limit: Optional[int] = Field(100, description="Results limit", ge=1, le=1000)
    offset: Optional[int] = Field(0, description="Results offset", ge=0)