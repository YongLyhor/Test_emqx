from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.models.device import Device
from app.repository.base import BaseRepository
from app.core.exceptions import DatabaseError, DeviceNotFoundError, DeviceAlreadyExistsError
from app.core.logging import logger

class DeviceRepository(BaseRepository[Device]):
    """Repository for device operations"""
    
    def __init__(self, db: Session):
        super().__init__(Device, db)
    
    def get_by_device_id(self, device_id: str) -> Optional[Device]:
        """Get device by its device_id"""
        try:
            return self.db.query(self.model).filter(
                self.model.device_id == device_id
            ).first()
        except Exception as e:
            logger.error(f"Error fetching device {device_id}: {e}")
            raise DatabaseError(f"Failed to fetch device: {str(e)}")
    
    def create_device(self, **kwargs) -> Device:
        """Create a new device with duplicate check"""
        try:
            # Check if device already exists
            existing = self.get_by_device_id(kwargs.get('device_id'))
            if existing:
                raise DeviceAlreadyExistsError(kwargs.get('device_id'))
            return self.create(**kwargs)
        except DeviceAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"Error creating device: {e}")
            raise DatabaseError(f"Failed to create device: {str(e)}")
    
    def get_by_sensor_type(
        self, 
        sensor_type: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Device]:
        """Get devices by sensor type"""
        try:
            query = self.db.query(self.model).filter(
                self.model.sensor_type == sensor_type
            )
            if status:
                query = query.filter(self.model.status == status)
            return query.offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching devices by type {sensor_type}: {e}")
            raise DatabaseError(f"Failed to fetch devices: {str(e)}")
    
    def get_active_devices(self, sensor_type: Optional[str] = None) -> List[Device]:
        """Get all active devices"""
        try:
            query = self.db.query(self.model).filter(
                self.model.status == 'active'
            )
            if sensor_type:
                query = query.filter(self.model.sensor_type == sensor_type)
            return query.all()
        except Exception as e:
            logger.error(f"Error fetching active devices: {e}")
            raise DatabaseError(f"Failed to fetch active devices: {str(e)}")
    
    def get_by_building(self, building: str) -> List[Device]:
        """Get devices by building"""
        try:
            return self.db.query(self.model).filter(
                self.model.building == building
            ).all()
        except Exception as e:
            logger.error(f"Error fetching devices in building {building}: {e}")
            raise DatabaseError(f"Failed to fetch devices: {str(e)}")
    
    def update_status(self, device_id: str, status: str) -> Device:
        """Update device status"""
        try:
            device = self.get_by_device_id(device_id)
            if not device:
                raise DeviceNotFoundError(device_id)
            return self.update(device.id, status=status)
        except DeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating device status {device_id}: {e}")
            raise DatabaseError(f"Failed to update device status: {str(e)}")
    
    def search_devices(
        self,
        search_term: str,
        sensor_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Device]:
        """Search devices by name or device_id"""
        try:
            query = self.db.query(self.model).filter(
                or_(
                    self.model.name.ilike(f"%{search_term}%"),
                    self.model.device_id.ilike(f"%{search_term}%")
                )
            )
            if sensor_type:
                query = query.filter(self.model.sensor_type == sensor_type)
            if status:
                query = query.filter(self.model.status == status)
            return query.offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"Error searching devices: {e}")
            raise DatabaseError(f"Failed to search devices: {str(e)}")
    
    def get_device_with_stats(self, device_id: str) -> Dict[str, Any]:
        """Get device with statistics"""
        try:
            from app.models.sensor_reading import SensorReading
            from sqlalchemy import func
            
            device = self.get_by_device_id(device_id)
            if not device:
                raise DeviceNotFoundError(device_id)
            
            # Get statistics
            stats = self.db.query(
                func.count(SensorReading.id).label('total_readings'),
                func.avg(SensorReading.value).label('avg_value'),
                func.min(SensorReading.value).label('min_value'),
                func.max(SensorReading.value).label('max_value'),
                func.avg(SensorReading.quality).label('avg_quality'),
                func.max(SensorReading.time).label('last_reading_time')
            ).filter(SensorReading.device_id == device_id).first()
            
            # Get last reading
            last_reading = self.db.query(SensorReading).filter(
                SensorReading.device_id == device_id
            ).order_by(desc(SensorReading.time)).first()
            
            # Build response
            result = {
                "device": device,
                "stats": {
                    "total_readings": stats.total_readings or 0,
                    "avg_value": float(stats.avg_value) if stats.avg_value else None,
                    "min_value": float(stats.min_value) if stats.min_value else None,
                    "max_value": float(stats.max_value) if stats.max_value else None,
                    "avg_quality": float(stats.avg_quality) if stats.avg_quality else None,
                    "last_reading_time": stats.last_reading_time
                }
            }
            
            if last_reading:
                result["last_reading"] = {
                    "value": float(last_reading.value),
                    "unit": last_reading.unit,
                    "time": last_reading.time,
                    "quality": last_reading.quality
                }
                
                # Calculate minutes since last reading
                from datetime import datetime, timezone
                if last_reading.time:
                    now = datetime.now(timezone.utc)
                    minutes = (now - last_reading.time).total_seconds() / 60
                    result["is_online"] = minutes < 15
                    result["minutes_since_last_reading"] = int(minutes)
                else:
                    result["is_online"] = False
                    result["minutes_since_last_reading"] = None
            else:
                result["is_online"] = False
                result["minutes_since_last_reading"] = None
                result["last_reading"] = None
            
            return result
        except DeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting device stats {device_id}: {e}")
            raise DatabaseError(f"Failed to get device stats: {str(e)}")