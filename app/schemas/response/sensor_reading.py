from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal

class SensorReadingResponse(BaseModel):
    """Response schema for sensor reading"""
    id: int = Field(..., description="Reading ID")
    time: datetime = Field(..., description="Reading timestamp")
    sensor_type: str = Field(..., description="Sensor type")
    device_id: str = Field(..., description="Device identifier")
    value: float = Field(..., description="Reading value")
    unit: str = Field(..., description="Unit of measurement")
    quality: int = Field(..., description="Data quality (0-100)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "time": "2026-08-27T10:00:00Z",
                "sensor_type": "water",
                "device_id": "WTR-001-BLDG-A",
                "value": 245.678,
                "unit": "m³",
                "quality": 100,
                "metadata": {"flow_rate": 0.42},
                "created_at": "2026-08-27T10:00:00Z"
            }
        }

class SensorReadingDetailResponse(SensorReadingResponse):
    """Detailed response for sensor reading"""
    device_name: Optional[str] = Field(None, description="Device name")
    device_location: Optional[str] = Field(None, description="Device location")
    sensor_type_display: Optional[str] = Field(None, description="Sensor type display name")

class SensorReadingAggregatedResponse(BaseModel):
    """Response schema for aggregated readings"""
    bucket: datetime = Field(..., description="Time bucket")
    device_id: Optional[str] = Field(None, description="Device identifier")
    avg_value: Optional[float] = Field(None, description="Average value")
    max_value: Optional[float] = Field(None, description="Maximum value")
    min_value: Optional[float] = Field(None, description="Minimum value")
    sum_value: Optional[float] = Field(None, description="Sum of values")
    count: Optional[int] = Field(None, description="Number of readings")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "bucket": "2026-08-27T10:00:00Z",
                "device_id": "WTR-001-BLDG-A",
                "avg_value": 245.678,
                "max_value": 246.123,
                "min_value": 245.234,
                "sum_value": 1474.068,
                "count": 6
            }
        }

class SensorReadingStatisticsResponse(BaseModel):
    """Response schema for sensor reading statistics"""
    sensor_type: str = Field(..., description="Sensor type")
    device_id: Optional[str] = Field(None, description="Device identifier")
    total_readings: int = Field(..., description="Total number of readings")
    avg_value: float = Field(..., description="Average value")
    max_value: float = Field(..., description="Maximum value")
    min_value: float = Field(..., description="Minimum value")
    sum_value: float = Field(..., description="Sum of values")
    stddev_value: Optional[float] = Field(None, description="Standard deviation")
    start_time: datetime = Field(..., description="Start time of data range")
    end_time: datetime = Field(..., description="End time of data range")
    
    class Config:
        from_attributes = True