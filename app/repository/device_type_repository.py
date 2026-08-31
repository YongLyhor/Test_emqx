from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.device_type import DeviceType
from app.repository.base import BaseRepository
from app.core.exceptions import DatabaseError, RecordNotFoundError
from app.core.logging import logger

class DeviceTypeRepository(BaseRepository[DeviceType]):
    """Repository for device type operations"""
    
    def __init__(self, db: Session):
        super().__init__(DeviceType, db)
    
    def get_by_code(self, type_code: str) -> Optional[DeviceType]:
        """Get device type by code"""
        try:
            return self.db.query(self.model).filter(
                self.model.type_code == type_code
            ).first()
        except Exception as e:
            logger.error(f"Error fetching device type {type_code}: {e}")
            raise DatabaseError(f"Failed to fetch device type: {str(e)}")
    
    def get_active_types(self) -> List[DeviceType]:
        """Get all active device types"""
        try:
            return self.db.query(self.model).filter(
                self.model.is_active == True
            ).all()
        except Exception as e:
            logger.error(f"Error fetching active device types: {e}")
            raise DatabaseError(f"Failed to fetch active device types: {str(e)}")
    
    def get_by_default_unit(self, unit: str) -> List[DeviceType]:
        """Get device types by default unit"""
        try:
            return self.db.query(self.model).filter(
                self.model.default_unit == unit
            ).all()
        except Exception as e:
            logger.error(f"Error fetching device types by unit {unit}: {e}")
            raise DatabaseError(f"Failed to fetch device types: {str(e)}")
    
    def validate_sensor_type(self, sensor_type: str) -> bool:
        """Validate if sensor type exists and is active"""
        try:
            device_type = self.get_by_code(sensor_type)
            return device_type is not None and device_type.is_active
        except Exception as e:
            logger.error(f"Error validating sensor type {sensor_type}: {e}")
            return False
    
    def get_units_by_type(self, sensor_type: str) -> List[str]:
        """Get allowed units for a sensor type"""
        try:
            device_type = self.get_by_code(sensor_type)
            if device_type:
                return [device_type.default_unit]
            return []
        except Exception as e:
            logger.error(f"Error getting units for {sensor_type}: {e}")
            return []
    
    def get_alert_threshold(self, sensor_type: str) -> Optional[float]:
        """Get alert threshold for a sensor type"""
        try:
            device_type = self.get_by_code(sensor_type)
            if device_type:
                return float(device_type.alert_threshold) if device_type.alert_threshold else None
            return None
        except Exception as e:
            logger.error(f"Error getting alert threshold for {sensor_type}: {e}")
            return None