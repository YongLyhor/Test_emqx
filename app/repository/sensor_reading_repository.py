from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, text
from app.models.sensor_reading import SensorReading
from app.repository.base import BaseRepository 
from app.core.exceptions import DatabaseError
from app.core.logging import logger

class SensorReadingRepository(BaseRepository[SensorReading]):  
    """Repository for sensor reading operations"""
    
    def __init__(self, db: Session):
        super().__init__(SensorReading, db)
    
    def get_by_device_id(
        self, 
        device_id: str, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SensorReading]:
        """Get readings for a specific device with time range"""
        try:
            query = self.db.query(self.model).filter(
                self.model.device_id == device_id
            )
            
            if start_time:
                query = query.filter(self.model.time >= start_time)
            if end_time:
                query = query.filter(self.model.time <= end_time)
            
            return query.order_by(desc(self.model.time)).offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching readings for device {device_id}: {e}")
            raise DatabaseError(f"Failed to fetch device readings: {str(e)}")
    
    def get_latest_by_device(self, device_id: str) -> Optional[SensorReading]:
        """Get the latest reading for a device"""
        try:
            return self.db.query(self.model).filter(
                self.model.device_id == device_id
            ).order_by(desc(self.model.time)).first()
        except Exception as e:
            logger.error(f"Error fetching latest reading for device {device_id}: {e}")
            raise DatabaseError(f"Failed to fetch latest reading: {str(e)}")
    
    def get_latest_by_type(self, sensor_type: str, limit: int = 10) -> List[SensorReading]:
        """Get latest readings for a sensor type"""
        try:
            return self.db.query(self.model).filter(
                self.model.sensor_type == sensor_type
            ).order_by(desc(self.model.time)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching latest readings for type {sensor_type}: {e}")
            raise DatabaseError(f"Failed to fetch latest readings: {str(e)}")
    
    def get_aggregated(
        self,
        sensor_type: str,
        time_bucket: str,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get aggregated readings using time_bucket"""
        try:
            query = self.db.query(
                text(f"time_bucket(:time_bucket, time) AS bucket").bindparams(time_bucket=time_bucket),
                func.avg(self.model.value).label('avg_value'),
                func.max(self.model.value).label('max_value'),
                func.min(self.model.value).label('min_value'),
                func.count(self.model.id).label('sample_count')
            ).filter(
                self.model.sensor_type == sensor_type,
                self.model.time >= start_time,
                self.model.time <= end_time
            )
            
            if device_id:
                query = query.filter(self.model.device_id == device_id)
            
            query = query.group_by(text("bucket")).order_by(text("bucket DESC"))
            
            result = query.all()
            return [
                {
                    "bucket": row.bucket,
                    "avg_value": float(row.avg_value) if row.avg_value else None,
                    "max_value": float(row.max_value) if row.max_value else None,
                    "min_value": float(row.min_value) if row.min_value else None,
                    "sample_count": row.sample_count
                }
                for row in result
            ]
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
        """Get statistics for a sensor type"""
        try:
            query = self.db.query(
                func.count(self.model.id).label('total_readings'),
                func.avg(self.model.value).label('avg_value'),
                func.max(self.model.value).label('max_value'),
                func.min(self.model.value).label('min_value'),
                func.sum(self.model.value).label('sum_value'),
                func.stddev(self.model.value).label('stddev_value')
            ).filter(
                self.model.sensor_type == sensor_type,
                self.model.time >= start_time,
                self.model.time <= end_time
            )
            
            if device_id:
                query = query.filter(self.model.device_id == device_id)
            
            result = query.first()
            
            return {
                "sensor_type": sensor_type,
                "device_id": device_id,
                "total_readings": result.total_readings or 0,
                "avg_value": float(result.avg_value) if result.avg_value else 0,
                "max_value": float(result.max_value) if result.max_value else 0,
                "min_value": float(result.min_value) if result.min_value else 0,
                "sum_value": float(result.sum_value) if result.sum_value else 0,
                "stddev_value": float(result.stddev_value) if result.stddev_value else None,
                "start_time": start_time,
                "end_time": end_time
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise DatabaseError(f"Failed to get statistics: {str(e)}")
    
    def get_latest_by_all_devices(self) -> List[Dict[str, Any]]:
        """Get latest reading for each device"""
        try:
            query = text("""
                SELECT DISTINCT ON (device_id) 
                    device_id,
                    sensor_type,
                    value,
                    unit,
                    time,
                    quality,
                    metadata
                FROM sensor_readings
                ORDER BY device_id, time DESC
            """)
            result = self.db.execute(query).all()
            return [
                {
                    "device_id": row.device_id,
                    "sensor_type": row.sensor_type,
                    "value": float(row.value),
                    "unit": row.unit,
                    "time": row.time,
                    "quality": row.quality,
                    "metadata": row.metadata
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error fetching latest readings: {e}")
            raise DatabaseError(f"Failed to fetch latest readings: {str(e)}")
    
    def get_anomalies(
        self,
        sensor_type: str,
        threshold: float = 3.0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[SensorReading]:
        """Detect anomalous readings using Z-score"""
        try:
            stats_query = self.db.query(
                func.avg(self.model.value).label('mean'),
                func.stddev(self.model.value).label('stddev')
            ).filter(self.model.sensor_type == sensor_type)
            
            if start_time:
                stats_query = stats_query.filter(self.model.time >= start_time)
            if end_time:
                stats_query = stats_query.filter(self.model.time <= end_time)
            
            stats = stats_query.first()
            
            if not stats or not stats.stddev or stats.stddev == 0:
                return []
            
            mean = stats.mean
            stddev = stats.stddev
            
            query = self.db.query(self.model).filter(
                self.model.sensor_type == sensor_type,
                func.abs(self.model.value - mean) > threshold * stddev
            )
            
            if start_time:
                query = query.filter(self.model.time >= start_time)
            if end_time:
                query = query.filter(self.model.time <= end_time)
            
            return query.order_by(desc(self.model.time)).all()
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise DatabaseError(f"Failed to detect anomalies: {str(e)}")
    
    def delete_old_readings(self, days: int = 30) -> int:
        """Delete readings older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = self.db.query(self.model).filter(
                self.model.time < cutoff_date
            ).delete(synchronize_session=False)
            self.db.commit()
            logger.info(f"Deleted {deleted} readings older than {days} days")
            return deleted
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting old readings: {e}")
            raise DatabaseError(f"Failed to delete old readings: {str(e)}")