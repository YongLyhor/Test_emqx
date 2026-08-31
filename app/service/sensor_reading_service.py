from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repository.sensor_reading_repository import SensorReadingRepository
from app.repository.device_repository import DeviceRepository
from app.repository.device_type_repository import DeviceTypeRepository
from app.repository.alert_repository import AlertRepository
from app.service.base import BaseService
from app.core.exceptions import (
    ValidationError, 
    DeviceNotFoundError, 
    InvalidSensorTypeError,
    InvalidReadingError,
    DatabaseError
)
from app.core.logging import logger

class SensorReadingService(BaseService[SensorReadingRepository]):
    """Service for sensor reading business logic"""
    
    def __init__(self, db: Session):
        super().__init__(SensorReadingRepository(db), db)
        self.device_repo = DeviceRepository(db)
        self.device_type_repo = DeviceTypeRepository(db)
        self.alert_repo = AlertRepository(db)
    
    def validate_create(self, **kwargs) -> None:
        """Validate sensor reading before creation"""
        # Validate device exists
        device = self.device_repo.get_by_device_id(kwargs.get('device_id'))
        if not device:
            raise DeviceNotFoundError(kwargs.get('device_id'))
        
        
        sensor_type = kwargs.get('sensor_type')
        if not self.device_type_repo.validate_sensor_type(sensor_type):
            raise InvalidSensorTypeError(sensor_type)
        
        # Validate value range
        value = kwargs.get('value')
        if value is not None:
            device_type = self.device_type_repo.get_by_code(sensor_type)
            if device_type:
                min_val = device_type.min_value
                max_val = device_type.max_value
                if min_val is not None and value < min_val:
                    raise InvalidReadingError(f"Value {value} below minimum {min_val}")
                if max_val is not None and value > max_val:
                    raise InvalidReadingError(f"Value {value} exceeds maximum {max_val}")
        
        # Validate quality
        quality = kwargs.get('quality', 100)
        if quality < 0 or quality > 100:
            raise ValidationError("Quality must be between 0 and 100")
    
    def process_reading(self, reading_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming sensor reading - main entry point for MQTT"""
        try:
            # Validate
            self.validate_create(**reading_data)
            
            # Create reading
            reading = self.repository.create(**reading_data)
            
            # Check for threshold alerts
            self._check_threshold_alert(reading)
            
            # Check for anomalies
            self._check_anomaly(reading)
            
            return {
                "success": True,
                "reading_id": reading.id,
                "message": "Reading processed successfully"
            }
        except Exception as e:
            logger.error(f"Error processing reading: {e}")
            raise
    
    def _check_threshold_alert(self, reading) -> None:
        """Check if reading exceeds threshold and create alert"""
        try:
            device_type = self.device_type_repo.get_by_code(reading.sensor_type)
            if not device_type or not device_type.alert_threshold:
                return
            
            threshold = float(device_type.alert_threshold)
            value = float(reading.value)
            
            if value > threshold:
                # Create alert
                self.alert_repo.create_alert(
                    device_id=reading.device_id,
                    sensor_type=reading.sensor_type,
                    alert_type='threshold_exceeded',
                    severity='warning' if value < threshold * 1.5 else 'critical',
                    message=f"Sensor reading {value} {reading.unit} exceeded threshold {threshold} {reading.unit}",
                    value=value,
                    threshold_value=threshold
                )
                logger.info(f"Threshold alert created for device {reading.device_id}")
        except Exception as e:
            logger.error(f"Error checking threshold alert: {e}")
    
    def _check_anomaly(self, reading) -> None:
        """Check if reading is anomalous using Z-score"""
        try:
            # Get recent readings for same device
            recent_readings = self.repository.get_by_device_id(
                reading.device_id,
                start_time=datetime.utcnow() - timedelta(hours=24),
                limit=100
            )
            
            if len(recent_readings) < 10:  # Not enough data
                return
            
            # Calculate mean and stddev
            values = [float(r.value) for r in recent_readings]
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            stddev = variance ** 0.5
            
            if stddev == 0:
                return
            
            z_score = abs(float(reading.value) - mean) / stddev
            
            if z_score > 3.0:  # Anomaly detected
                self.alert_repo.create_alert(
                    device_id=reading.device_id,
                    sensor_type=reading.sensor_type,
                    alert_type='anomaly_detected',
                    severity='warning' if z_score < 5.0 else 'critical',
                    message=f"Anomaly detected: Z-score {z_score:.2f} for value {reading.value}",
                    value=float(reading.value),
                    threshold_value=mean + 3 * stddev
                )
                logger.info(f"Anomaly alert created for device {reading.device_id}")
        except Exception as e:
            logger.error(f"Error checking anomaly: {e}")
    
    def get_readings(
        self,
        device_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get readings with filters"""
        try:
            if device_id:
                readings = self.repository.get_by_device_id(
                    device_id, start_time, end_time, limit, offset
                )
                total = self.repository.count(device_id=device_id)
            else:
                filters = {}
                if sensor_type:
                    filters['sensor_type'] = sensor_type
                if start_time:
                    filters['time >= start_time'] = start_time
                if end_time:
                    filters['time <= end_time'] = end_time
                
                readings = self.repository.get_all(skip=offset, limit=limit, **filters)
                total = self.repository.count(**filters)
            
            return {
                "items": [self._serialize_reading(r) for r in readings],
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        except Exception as e:
            logger.error(f"Error getting readings: {e}")
            raise DatabaseError(f"Failed to get readings: {str(e)}")
    
    @staticmethod
    def _serialize_reading(r) -> Dict[str, Any]:
        """Convert a SensorReading ORM object to a serializable dict"""
        return {
            "id": r.id,
            "device_id": r.device_id,
            "sensor_type": r.sensor_type,
            "value": float(r.value),
            "unit": r.unit,
            "time": r.time.isoformat() if r.time else None,
            "quality": r.quality,
            "metadata": r.metadata_,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
    
    def get_latest_by_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get latest reading for a device"""
        try:
            reading = self.repository.get_latest_by_device(device_id)
            if not reading:
                return None
            
            return {
                "device_id": reading.device_id,
                "sensor_type": reading.sensor_type,
                "value": float(reading.value),
                "unit": reading.unit,
                "time": reading.time,
                "quality": reading.quality,
                "metadata": reading.metadata_
            }
        except Exception as e:
            logger.error(f"Error getting latest reading: {e}")
            raise DatabaseError(f"Failed to get latest reading: {str(e)}")
    
    def get_aggregated(
        self,
        sensor_type: str,
        time_bucket: str,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get aggregated readings"""
        try:
            return self.repository.get_aggregated(
                sensor_type, time_bucket, start_time, end_time, device_id
            )
        except Exception as e:
            logger.error(f"Error getting aggregated data: {e}")
            raise DatabaseError(f"Failed to get aggregated data: {str(e)}")
    
    def get_statistics(
        self,
        sensor_type: str,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics for sensor readings"""
        try:
            return self.repository.get_statistics(
                sensor_type, start_time, end_time, device_id
            )
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise DatabaseError(f"Failed to get statistics: {str(e)}")
    
    def get_latest_all_devices(self) -> List[Dict[str, Any]]:
        """Get latest reading for all devices"""
        try:
            return self.repository.get_latest_by_all_devices()
        except Exception as e:
            logger.error(f"Error getting latest readings: {e}")
            raise DatabaseError(f"Failed to get latest readings: {str(e)}")
    
    def get_anomalies(
        self,
        sensor_type: str,
        threshold: float = 3.0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get anomalous readings"""
        try:
            anomalies = self.repository.get_anomalies(
                sensor_type, threshold, start_time, end_time
            )
            return [
                {
                    "id": a.id,
                    "device_id": a.device_id,
                    "time": a.time,
                    "value": float(a.value),
                    "unit": a.unit,
                    "quality": a.quality,
                    "metadata": a.metadata_
                }
                for a in anomalies
            ]
        except Exception as e:
            logger.error(f"Error getting anomalies: {e}")
            raise DatabaseError(f"Failed to get anomalies: {str(e)}")