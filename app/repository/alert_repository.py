from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.alert import Alert
from app.repository.base import BaseRepository
from app.core.exceptions import DatabaseError, RecordNotFoundError
from app.core.logging import logger

class AlertRepository(BaseRepository[Alert]):
    """Repository for alert operations"""
    
    def __init__(self, db: Session):
        super().__init__(Alert, db)
    
    def get_by_device(
        self,
        device_id: str,
        resolved: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Alert]:
        """Get alerts by device"""
        try:
            query = self.db.query(self.model).filter(
                self.model.device_id == device_id
            )
            if resolved is not None:
                query = query.filter(self.model.resolved == resolved)
            return query.order_by(desc(self.model.created_at)).offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching alerts for device {device_id}: {e}")
            raise DatabaseError(f"Failed to fetch alerts: {str(e)}")
    
    def get_by_severity(
        self,
        severity: str,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alerts by severity"""
        try:
            query = self.db.query(self.model).filter(
                self.model.severity == severity
            )
            if resolved is not None:
                query = query.filter(self.model.resolved == resolved)
            return query.order_by(desc(self.model.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching alerts by severity {severity}: {e}")
            raise DatabaseError(f"Failed to fetch alerts: {str(e)}")
    
    def get_unresolved(self, sensor_type: Optional[str] = None) -> List[Alert]:
        """Get all unresolved alerts"""
        try:
            query = self.db.query(self.model).filter(
                self.model.resolved == False
            )
            if sensor_type:
                query = query.filter(self.model.sensor_type == sensor_type)
            return query.order_by(desc(self.model.severity), desc(self.model.created_at)).all()
        except Exception as e:
            logger.error(f"Error fetching unresolved alerts: {e}")
            raise DatabaseError(f"Failed to fetch unresolved alerts: {str(e)}")
    
    def resolve_alert(self, alert_id: int, resolved_at: Optional[datetime] = None) -> Alert:
        """Resolve an alert"""
        try:
            alert = self.get_by_id(alert_id)
            if not alert:
                raise RecordNotFoundError("Alert", alert_id)
            
            if resolved_at is None:
                resolved_at = datetime.utcnow()
            
            return self.update(alert_id, resolved=True, resolved_at=resolved_at)
        except RecordNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            raise DatabaseError(f"Failed to resolve alert: {str(e)}")
    
    def create_alert(self, **kwargs) -> Alert:
        """Create a new alert"""
        try:
            # Check if similar unresolved alert exists
            existing = self.db.query(self.model).filter(
                self.model.device_id == kwargs.get('device_id'),
                self.model.alert_type == kwargs.get('alert_type'),
                self.model.resolved == False
            ).first()
            
            if existing:
                logger.info(f"Alert already exists for device {kwargs.get('device_id')}")
                return existing
            
            return self.create(**kwargs)
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            raise DatabaseError(f"Failed to create alert: {str(e)}")
    
    def get_alert_stats(
        self,
        sensor_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            from sqlalchemy import func
            
            query = self.db.query(
                func.count(self.model.id).label('total'),
                func.sum(func.cast(self.model.resolved, type_=int)).label('resolved_count')
            )
            
            if sensor_type:
                query = query.filter(self.model.sensor_type == sensor_type)
            if start_time:
                query = query.filter(self.model.created_at >= start_time)
            if end_time:
                query = query.filter(self.model.created_at <= end_time)
            
            result = query.first()
            
            # Get breakdown by severity
            severity_query = self.db.query(
                self.model.severity,
                func.count(self.model.id).label('count')
            )
            if sensor_type:
                severity_query = severity_query.filter(self.model.sensor_type == sensor_type)
            if start_time:
                severity_query = severity_query.filter(self.model.created_at >= start_time)
            if end_time:
                severity_query = severity_query.filter(self.model.created_at <= end_time)
            
            severity_breakdown = severity_query.group_by(self.model.severity).all()
            
            return {
                "total_alerts": result.total or 0,
                "resolved_alerts": result.resolved_count or 0,
                "unresolved_alerts": (result.total or 0) - (result.resolved_count or 0),
                "severity_breakdown": [
                    {"severity": row.severity, "count": row.count}
                    for row in severity_breakdown
                ]
            }
        except Exception as e:
            logger.error(f"Error getting alert stats: {e}")
            raise DatabaseError(f"Failed to get alert stats: {str(e)}")