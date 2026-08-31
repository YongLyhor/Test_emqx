from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class AlertCreate(BaseModel):
    """Request schema for creating an alert"""
    device_id: str = Field(..., description="Device identifier")
    sensor_type: str = Field(..., description="Sensor type")
    alert_type: str = Field(..., description="Alert type: threshold_exceeded, connection_lost, anomaly_detected")
    severity: str = Field(..., description="Severity: info, warning, critical")
    message: str = Field(..., description="Alert message")
    value: Optional[float] = Field(None, description="Value that triggered alert")
    threshold_value: Optional[float] = Field(None, description="Threshold that was exceeded")
    
    @validator('severity')
    def validate_severity(cls, v):
        allowed = ['info', 'warning', 'critical']
        if v.lower() not in allowed:
            raise ValueError(f'severity must be one of: {allowed}')
        return v.lower()
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        allowed = ['threshold_exceeded', 'connection_lost', 'anomaly_detected', 'status_change']
        if v.lower() not in allowed:
            raise ValueError(f'alert_type must be one of: {allowed}')
        return v.lower()

class AlertResolveRequest(BaseModel):
    """Request schema for resolving an alert"""
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp (defaults to now)")

class AlertQueryParams(BaseModel):
    """Query parameters for filtering alerts"""
    device_id: Optional[str] = Field(None, description="Filter by device ID")
    sensor_type: Optional[str] = Field(None, description="Filter by sensor type")
    severity: Optional[str] = Field(None, description="Filter by severity")
    resolved: Optional[bool] = Field(None, description="Filter by resolved status")
    start_time: Optional[datetime] = Field(None, description="Start time (UTC)")
    end_time: Optional[datetime] = Field(None, description="End time (UTC)")
    limit: Optional[int] = Field(100, description="Results limit", ge=1, le=10000)
    offset: Optional[int] = Field(0, description="Results offset", ge=0)