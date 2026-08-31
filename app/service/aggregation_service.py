from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repository.aggregation_repository import AggregationRepository
from app.repository.sensor_reading_repository import SensorReadingRepository
from app.service.base import BaseService
from app.core.exceptions import DatabaseError
from app.core.logging import logger

class AggregationService(BaseService[AggregationRepository]):
    """Service for aggregation business logic"""
    
    def __init__(self, db: Session):
        super().__init__(AggregationRepository(db), db)
        self.reading_repo = SensorReadingRepository(db)
    
    def calculate_and_store_aggregations(
        self,
        sensor_type: str,
        period: str,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate and store aggregations for a period"""
        try:
            # Get aggregated data from readings
            time_bucket = self._get_time_bucket(period)
            aggregated = self.reading_repo.get_aggregated(
                sensor_type, time_bucket, start_time, end_time, device_id
            )
            
            if not aggregated:
                return {
                    "success": True,
                    "message": "No data to aggregate",
                    "records_created": 0
                }
            
            # Store aggregations
            created_count = 0
            for data in aggregated:
                self.repository.create_or_update(
                    sensor_type=sensor_type,
                    device_id=device_id,
                    time_bucket=data["bucket"],
                    period=period,
                    avg_value=data["avg_value"],
                    max_value=data["max_value"],
                    min_value=data["min_value"],
                    sum_value=data["sum_value"],
                    count=data["sample_count"]
                )
                created_count += 1
            
            return {
                "success": True,
                "message": f"Aggregations calculated and stored",
                "records_created": created_count,
                "period": period,
                "time_range": {
                    "start": start_time,
                    "end": end_time
                }
            }
        except Exception as e:
            logger.error(f"Error calculating aggregations: {e}")
            raise DatabaseError(f"Failed to calculate aggregations: {str(e)}")
    
    def get_aggregations(
        self,
        sensor_type: str,
        period: str,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stored aggregations"""
        try:
            aggregations = self.repository.get_by_period(
                sensor_type, period, start_time, end_time, device_id
            )
            
            return {
                "success": True,
                "items": aggregations,
                "count": len(aggregations),
                "period": period,
                "sensor_type": sensor_type
            }
        except Exception as e:
            logger.error(f"Error getting aggregations: {e}")
            raise DatabaseError(f"Failed to get aggregations: {str(e)}")
    
    def _get_time_bucket(self, period: str) -> str:
        """Get time bucket interval based on period"""
        bucket_map = {
            'minute': '1 minute',
            '5_minutes': '5 minutes',
            'hour': '1 hour',
            'day': '1 day',
            'week': '1 week',
            'month': '1 month'
        }
        return bucket_map.get(period, '1 hour')
    
    def run_scheduled_aggregations(self) -> Dict[str, Any]:
        """Run scheduled aggregations for all sensor types"""
        try:
            now = datetime.utcnow()
            results = {}
            
            sensor_types = ['water', 'electricity', 'gas', 'cooling']
            periods = ['hour', 'day', 'week']
            
            for sensor_type in sensor_types:
                for period in periods:
                    start_time = self._get_period_start(now, period)
                    
                    result = self.calculate_and_store_aggregations(
                        sensor_type=sensor_type,
                        period=period,
                        start_time=start_time,
                        end_time=now
                    )
                    
                    if sensor_type not in results:
                        results[sensor_type] = {}
                    results[sensor_type][period] = result["records_created"]
            
            return {
                "success": True,
                "message": "Scheduled aggregations completed",
                "results": results,
                "timestamp": now
            }
        except Exception as e:
            logger.error(f"Error running scheduled aggregations: {e}")
            raise DatabaseError(f"Failed to run scheduled aggregations: {str(e)}")
    
    def _get_period_start(self, now: datetime, period: str) -> datetime:
        """Get start time for a period"""
        if period == 'hour':
            return now - timedelta(hours=1)
        elif period == 'day':
            return now - timedelta(days=1)
        elif period == 'week':
            return now - timedelta(weeks=1)
        elif period == 'month':
            return now - timedelta(days=30)
        else:
            return now - timedelta(hours=1)