from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here
from app.models.sensor_reading import SensorReading
from app.models.device import Device
from app.models.device_type import DeviceType
from app.models.alert import Alert
from app.models.aggregation import DataAggregation
from app.models.audit_log import AuditLog

__all__ = [
    "Base",
    "SensorReading",
    "Device",
    "DeviceType",
    "Alert",
    "DataAggregation",
    "AuditLog"
]