from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.aggregation import DataAggregation
from app.repository.base import BaseRepository
from app.core.exceptions import DatabaseError
from app.core.logging import logger

class AggregationRepository(BaseRepository[DataAggregation]):
    """Repository for aggregation operations"""
    
    def __init__(self, db: Session):
        super().__init__(DataAggregation, db)
    
    def get_by_period(
        self,
        sensor_type: str,
        period: str,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[str] = None
    ) -> List[DataAggregation]:
        """Get aggregations by period"""
        try:
            query = self.db.query(self.model).filter(
                self.model.sensor_type == sensor_type,
                self.model.period == period,
                self.model.time_bucket >= start_time,
                self.model.time_bucket <= end_time
            )
            if device_id:
                query = query.filter(self.model.device_id == device_id)
            return query.order_by(self.model.time_bucket).all()
        except Exception as e:
            logger.error(f"Error fetching aggregations: {e}")
            raise DatabaseError(f"Failed to fetch aggregations: {str(e)}")
    
    def create_or_update(
        self,
        sensor_type: str,
        device_id: Optional[str],
        time_bucket: datetime,
        period: str,
        **kwargs
    ) -> DataAggregation:
        """Create or update an aggregation record"""
        try:
            existing = self.db.query(self.model).filter(
                self.model.sensor_type == sensor_type,
                self.model.device_id == device_id,
                self.model.time_bucket == time_bucket,
                self.model.period == period
            ).first()
            
            if existing:
                # Update existing
                for key, value in kwargs.items():
                    if value is not None and hasattr(existing, key):
                        setattr(existing, key, value)
                self.db.commit()
                self.db.refresh(existing)
                return existing
            else:
                # Create new
                return self.create(
                    sensor_type=sensor_type,
                    device_id=device_id,
                    time_bucket=time_bucket,
                    period=period,
                    **kwargs
                )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating/updating aggregation: {e}")
            raise DatabaseError(f"Failed to create/update aggregation: {str(e)}")
    
    def get_latest_period(self, sensor_type: str, period: str, device_id: Optional[str] = None) -> Optional[DataAggregation]:
        """Get the latest aggregation for a period"""
        try:
            query = self.db.query(self.model).filter(
                self.model.sensor_type == sensor_type,
                self.model.period == period
            )
            if device_id:
                query = query.filter(self.model.device_id == device_id)
            return query.order_by(self.model.time_bucket.desc()).first()
        except Exception as e:
            logger.error(f"Error fetching latest aggregation: {e}")
            return None