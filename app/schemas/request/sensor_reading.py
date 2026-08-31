from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal

class SensorReadingCreate(BaseModel):
    """Request schema for creating a single sensor reading"""
    time: Optional[datetime] = Field(None, description="Reading timestamp (UTC)")
    sensor_type: str = Field(..., description="Type of sensor: water, electricity, gas, cooling")
    device_id: str = Field(..., description="Unique device identifier")
    value: float = Field(..., description="Sensor reading value", gt=0)
    unit: str = Field(..., description="Unit of measurement")
    quality: Optional[int] = Field(100, description="Data quality (0-100)", ge=0, le=100)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('sensor_type')
    def validate_sensor_type(cls, v):
        allowed_types = ['water', 'electricity', 'gas', 'cooling']
        if v.lower() not in allowed_types:
            raise ValueError(f'sensor_type must be one of: {allowed_types}')
        return v.lower()
    
    @validator('unit')
    def validate_unit(cls, v, values):
        unit_map = {
            'water': ['m³'],
            'electricity': ['kWh'],
            'gas': ['m³/h'],
            'cooling': ['kW']
        }
        sensor_type = values.get('sensor_type')
        if sensor_type and v not in unit_map.get(sensor_type, []):
            allowed = unit_map.get(sensor_type, [])
            raise ValueError(f'unit must be one of: {allowed} for sensor type: {sensor_type}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "time": "2026-08-27T10:00:00Z",
                "sensor_type": "water",
                "device_id": "WTR-001-BLDG-A",
                "value": 245.678,
                "unit": "m³",
                "quality": 100,
                "metadata": {
                    "flow_rate": 0.42,
                    "pressure": 3.2
                }
            }
        }

class SensorReadingBatchCreate(BaseModel):
    """Request schema for creating multiple sensor readings"""
    readings: List[SensorReadingCreate] = Field(..., min_items=1, max_items=1000)

class SensorReadingQueryParams(BaseModel):
    """Query parameters for filtering sensor readings"""
    sensor_type: Optional[str] = Field(None, description="Filter by sensor type")
    device_id: Optional[str] = Field(None, description="Filter by device ID")
    start_time: Optional[datetime] = Field(None, description="Start time (UTC)")
    end_time: Optional[datetime] = Field(None, description="End time (UTC)")
    limit: Optional[int] = Field(100, description="Results limit", ge=1, le=10000)
    offset: Optional[int] = Field(0, description="Results offset", ge=0)
    min_value: Optional[float] = Field(None, description="Minimum value filter")
    max_value: Optional[float] = Field(None, description="Maximum value filter")
    min_quality: Optional[int] = Field(None, description="Minimum quality (0-100)", ge=0, le=100)