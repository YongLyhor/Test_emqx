from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.repository.alert_repository import AlertRepository
from app.repository.device_repository import DeviceRepository
from app.service.base import BaseService
from app.core.exceptions import ValidationError, RecordNotFoundError, DatabaseError
from app.core.logging import logger

class AlertService(BaseService[AlertRepository]):
    """Service for alert business logic"""
    
    def __init__(self, db: Session):
        super().__init__(AlertRepository(db), db)
        self.device_repo = DeviceRepository(db)
    
    def validate_create(self, **kwargs) -> None:
        """Validate alert before creation"""
        # Validate device exists
        device = self.device_repo.get_by_device_id(kwargs.get('device_id'))
        if not device:
            raise ValidationError(f"Device {kwargs.get('device_id')} not found")
        
        # Validate severity
        severity = kwargs.get('severity')
        if severity not in ['info', 'warning', 'critical']:
            raise ValidationError("Severity must be info, warning, or critical")
        
        # Validate alert type
        alert_type = kwargs.get('alert_type')
        allowed_types = ['threshold_exceeded', 'connection_lost', 'anomaly_detected', 'status_change']
        if alert_type not in allowed_types:
            raise ValidationError(f"Alert type must be one of: {allowed_types}")
    
    def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert"""
        try:
            self.validate_create(**alert_data)
            alert = self.repository.create_alert(**alert_data)
            return {
                "success": True,
                "alert": alert,
                "message": "Alert created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            raise
    
    def get_alerts(
        self,
        device_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get alerts with filters"""
        try:
            filters = {}
            if device_id:
                filters['device_id'] = device_id
            if sensor_type:
                filters['sensor_type'] = sensor_type
            if severity:
                filters['severity'] = severity
            if resolved is not None:
                filters['resolved'] = resolved
            if start_time:
                filters['created_at >= start_time'] = start_time
            if end_time:
                filters['created_at <= end_time'] = end_time
            
            alerts = self.repository.get_all(skip=offset, limit=limit, **filters)
            total = self.repository.count(**filters)
            
            return {
                "items": alerts,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            raise DatabaseError(f"Failed to get alerts: {str(e)}")
    
    def get_unresolved_alerts(self, sensor_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all unresolved alerts"""
        try:
            alerts = self.repository.get_unresolved(sensor_type)
            return [
                {
                    "id": a.id,
                    "device_id": a.device_id,
                    "sensor_type": a.sensor_type,
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "message": a.message,
                    "created_at": a.created_at
                }
                for a in alerts
            ]
        except Exception as e:
            logger.error(f"Error getting unresolved alerts: {e}")
            raise DatabaseError(f"Failed to get unresolved alerts: {str(e)}")
    
    def resolve_alert(self, alert_id: int, resolved_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Resolve an alert"""
        try:
            alert = self.repository.resolve_alert(alert_id, resolved_at)
            return {
                "success": True,
                "alert": alert,
                "message": "Alert resolved successfully"
            }
        except RecordNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            raise DatabaseError(f"Failed to resolve alert: {str(e)}")
    
    def get_alert_stats(
        self,
        sensor_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            return self.repository.get_alert_stats(sensor_type, start_time, end_time)
        except Exception as e:
            logger.error(f"Error getting alert stats: {e}")
            raise DatabaseError(f"Failed to get alert stats: {str(e)}")