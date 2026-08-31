from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID

class DeviceResponse(BaseModel):
    """Response schema for device (basic)"""
    id: UUID = Field(..., description="Internal device ID")
    device_id: str = Field(..., description="Device identifier")
    name: str = Field(..., description="Device name")
    sensor_type: str = Field(..., description="Sensor type")
    location: Optional[str] = Field(None, description="Device location")
    building: Optional[str] = Field(None, description="Building name")
    status: str = Field(..., description="Device status")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "device_id": "WTR-001-BLDG-A",
                "name": "Main Water Meter - Building A",
                "sensor_type": "water",
                "location": "Basement - Utility Room 101",
                "building": "Building A",
                "status": "active",
                "created_at": "2025-06-15T00:00:00Z"
            }
        }

class DeviceDetailResponse(DeviceResponse):
    """Detailed response schema for device"""
    floor: Optional[int] = Field(None, description="Floor number")
    room: Optional[str] = Field(None, description="Room identifier")
    installation_date: Optional[date] = Field(None, description="Installation date")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional device metadata")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "device_id": "WTR-001-BLDG-A",
                "name": "Main Water Meter - Building A",
                "sensor_type": "water",
                "location": "Basement - Utility Room 101",
                "building": "Building A",
                "floor": -1,
                "room": "Utility Room 101",
                "status": "active",
                "installation_date": "2025-06-15",
                "firmware_version": "v2.3.1",
                "metadata": {"manufacturer": "Siemens"},
                "created_at": "2025-06-15T00:00:00Z",
                "updated_at": "2025-06-15T00:00:00Z"
            }
        }

class DeviceWithStatsResponse(DeviceDetailResponse):
    """Device response with statistics"""
    last_reading_time: Optional[datetime] = Field(None, description="Time of last reading")
    last_value: Optional[float] = Field(None, description="Last reading value")
    total_readings: Optional[int] = Field(None, description="Total number of readings")
    avg_value: Optional[float] = Field(None, description="Average reading value")
    min_value: Optional[float] = Field(None, description="Minimum reading value")
    max_value: Optional[float] = Field(None, description="Maximum reading value")
    reading_quality_avg: Optional[float] = Field(None, description="Average reading quality")
    is_online: Optional[bool] = Field(None, description="Whether device is online (recent reading)")
    minutes_since_last_reading: Optional[int] = Field(None, description="Minutes since last reading")