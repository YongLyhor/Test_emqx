from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.repository.device_repository import DeviceRepository
from app.repository.device_type_repository import DeviceTypeRepository
from app.service.base import BaseService
from app.core.exceptions import (
    ValidationError,
    DeviceNotFoundError,
    DeviceAlreadyExistsError,
    InvalidSensorTypeError,
    DatabaseError
)
from app.core.logging import logger

class DeviceService(BaseService[DeviceRepository]):
    """Service for device business logic"""
    
    def __init__(self, db: Session):
        super().__init__(DeviceRepository(db), db)
        self.device_type_repo = DeviceTypeRepository(db)
    
    def validate_create(self, **kwargs) -> None:
        """Validate device before creation"""
        # Check if device already exists
        if self.repository.get_by_device_id(kwargs.get('device_id')):
            raise DeviceAlreadyExistsError(kwargs.get('device_id'))
        
        # Validate sensor type
        sensor_type = kwargs.get('sensor_type')
        if not self.device_type_repo.validate_sensor_type(sensor_type):
            raise InvalidSensorTypeError(sensor_type)
        
        # Validate status
        status = kwargs.get('status', 'active')
        if status not in ['active', 'inactive', 'maintenance']:
            raise ValidationError("Status must be active, inactive, or maintenance")
    
    def validate_update(self, id: Any, **kwargs) -> None:
        """Validate device before update"""
        # Check if device exists
        device = self.repository.get_by_id(id)
        if not device:
            raise DeviceNotFoundError(id)
        
        # Validate sensor type if changing
        sensor_type = kwargs.get('sensor_type')
        if sensor_type and not self.device_type_repo.validate_sensor_type(sensor_type):
            raise InvalidSensorTypeError(sensor_type)
        
        # Validate status if changing
        status = kwargs.get('status')
        if status and status not in ['active', 'inactive', 'maintenance']:
            raise ValidationError("Status must be active, inactive, or maintenance")
    
    def create_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new device"""
        try:
            self.validate_create(**device_data)
            device = self.repository.create_device(**device_data)
            return {
                "success": True,
                "device": device,
                "message": "Device created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating device: {e}")
            raise
    
    def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get device by device_id"""
        try:
            device = self.repository.get_by_device_id(device_id)
            if not device:
                raise DeviceNotFoundError(device_id)
            return {
                "success": True,
                "device": device
            }
        except DeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting device: {e}")
            raise DatabaseError(f"Failed to get device: {str(e)}")
    
    def get_device_with_stats(self, device_id: str) -> Dict[str, Any]:
        """Get device with statistics"""
        try:
            return self.repository.get_device_with_stats(device_id)
        except DeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting device stats: {e}")
            raise DatabaseError(f"Failed to get device stats: {str(e)}")
    
    def update_device(self, device_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a device"""
        try:
            device = self.repository.get_by_device_id(device_id)
            if not device:
                raise DeviceNotFoundError(device_id)
            
            self.validate_update(device.id, **update_data)
            updated = self.repository.update(device.id, **update_data)
            
            return {
                "success": True,
                "device": updated,
                "message": "Device updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating device: {e}")
            raise
    
    def delete_device(self, device_id: str) -> Dict[str, Any]:
        """Delete a device"""
        try:
            device = self.repository.get_by_device_id(device_id)
            if not device:
                raise DeviceNotFoundError(device_id)
            
            self.repository.delete(device.id)
            return {
                "success": True,
                "message": f"Device {device_id} deleted successfully"
            }
        except DeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting device: {e}")
            raise DatabaseError(f"Failed to delete device: {str(e)}")
    
    def update_device_status(self, device_id: str, status: str) -> Dict[str, Any]:
        """Update device status"""
        try:
            if status not in ['active', 'inactive', 'maintenance']:
                raise ValidationError("Status must be active, inactive, or maintenance")
            
            updated = self.repository.update_status(device_id, status)
            return {
                "success": True,
                "device": updated,
                "message": f"Device status updated to {status}"
            }
        except DeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating device status: {e}")
            raise
    
    def get_devices(
        self,
        sensor_type: Optional[str] = None,
        status: Optional[str] = None,
        building: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get devices with filters"""
        try:
            if search:
                devices = self.repository.search_devices(
                    search, sensor_type, status, limit, offset
                )
                total = len(devices)  # Simplified
            else:
                filters = {}
                if sensor_type:
                    filters['sensor_type'] = sensor_type
                if status:
                    filters['status'] = status
                if building:
                    filters['building'] = building
                
                devices = self.repository.get_all(skip=offset, limit=limit, **filters)
                total = self.repository.count(**filters)
            
            return {
                "items": [self._serialize_device(d) for d in devices],
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            raise DatabaseError(f"Failed to get devices: {str(e)}")
    
    @staticmethod
    def _serialize_device(d) -> Dict[str, Any]:
        """Convert a Device ORM object to a serializable dict"""
        return {
            "id": str(d.id),
            "device_id": d.device_id,
            "name": d.name,
            "sensor_type": d.sensor_type,
            "location": d.location,
            "building": d.building,
            "floor": d.floor,
            "room": d.room,
            "installation_date": str(d.installation_date) if d.installation_date else None,
            "firmware_version": d.firmware_version,
            "status": d.status,
            "metadata": d.metadata_,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None
        }
    
    def get_active_devices(self, sensor_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active devices"""
        try:
            devices = self.repository.get_active_devices(sensor_type)
            return [
                {
                    "device_id": d.device_id,
                    "name": d.name,
                    "sensor_type": d.sensor_type,
                    "location": d.location,
                    "status": d.status
                }
                for d in devices
            ]
        except Exception as e:
            logger.error(f"Error getting active devices: {e}")
            raise DatabaseError(f"Failed to get active devices: {str(e)}")