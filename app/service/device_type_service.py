from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.repository.device_type_repository import DeviceTypeRepository
from app.service.base import BaseService
from app.core.exceptions import ValidationError, RecordNotFoundError, DatabaseError
from app.core.logging import logger

class DeviceTypeService(BaseService[DeviceTypeRepository]):
    """Service for device type business logic"""
    
    def __init__(self, db: Session):
        super().__init__(DeviceTypeRepository(db), db)
    
    def validate_create(self, **kwargs) -> None:
        """Validate device type before creation"""
        # Check if type code already exists
        if self.repository.get_by_code(kwargs.get('type_code')):
            raise ValidationError(f"Type code {kwargs.get('type_code')} already exists")
        
        # Validate alert threshold
        alert_threshold = kwargs.get('alert_threshold')
        min_val = kwargs.get('min_value')
        max_val = kwargs.get('max_value')
        
        if alert_threshold is not None:
            if min_val is not None and alert_threshold < min_val:
                raise ValidationError("Alert threshold cannot be less than minimum value")
            if max_val is not None and alert_threshold > max_val:
                raise ValidationError("Alert threshold cannot be greater than maximum value")
    
    def get_by_code(self, type_code: str) -> Dict[str, Any]:
        """Get device type by code"""
        try:
            device_type = self.repository.get_by_code(type_code)
            if not device_type:
                raise RecordNotFoundError("DeviceType", type_code)
            return {
                "success": True,
                "device_type": device_type
            }
        except RecordNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting device type: {e}")
            raise DatabaseError(f"Failed to get device type: {str(e)}")
    
    def get_active_types(self) -> List[Dict[str, Any]]:
        """Get all active device types"""
        try:
            types = self.repository.get_active_types()
            return [
                {
                    "type_code": t.type_code,
                    "display_name": t.display_name,
                    "default_unit": t.default_unit,
                    "alert_threshold": float(t.alert_threshold) if t.alert_threshold else None
                }
                for t in types
            ]
        except Exception as e:
            logger.error(f"Error getting active types: {e}")
            raise DatabaseError(f"Failed to get active types: {str(e)}")
    
    def validate_sensor_type(self, sensor_type: str) -> bool:
        """Validate if sensor type exists"""
        try:
            return self.repository.validate_sensor_type(sensor_type)
        except Exception as e:
            logger.error(f"Error validating sensor type: {e}")
            return False
    
    def get_alert_threshold(self, sensor_type: str) -> Optional[float]:
        """Get alert threshold for a sensor type"""
        try:
            return self.repository.get_alert_threshold(sensor_type)
        except Exception as e:
            logger.error(f"Error getting alert threshold: {e}")
            return None