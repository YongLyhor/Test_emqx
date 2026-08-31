from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AlertResponse(BaseModel):
    """Response schema for alert"""
    id: int = Field(..., description="Alert ID")
    device_id: str = Field(..., description="Device identifier")
    sensor_type: str = Field(..., description="Sensor type")
    alert_type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="Severity level")
    message: str = Field(..., description="Alert message")
    resolved: bool = Field(..., description="Is resolved")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "device_id": "ELC-003-FLOOR-2",
                "sensor_type": "electricity",
                "alert_type": "threshold_exceeded",
                "severity": "warning",
                "message": "Energy consumption exceeded threshold of 50,000 kWh",
                "resolved": False,
                "created_at": "2026-08-27T10:00:00Z"
            }
        }

class AlertDetailResponse(AlertResponse):
    """Detailed response schema for alert"""
    value: Optional[float] = Field(None, description="Value that triggered alert")
    threshold_value: Optional[float] = Field(None, description="Threshold that was exceeded")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    device_name: Optional[str] = Field(None, description="Device name")
    device_location: Optional[str] = Field(None, description="Device location")