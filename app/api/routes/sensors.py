from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.service.sensor_reading_service import SensorReadingService
from app.schemas.request.sensor_reading import (
    SensorReadingCreate,
    SensorReadingBatchCreate,
    SensorReadingQueryParams
)
from app.schemas.response.sensor_reading import (
    SensorReadingResponse,
    SensorReadingDetailResponse,
    SensorReadingAggregatedResponse,
    SensorReadingStatisticsResponse
)
from app.schemas.response.common import PaginatedResponse, SuccessResponse, ErrorResponse
from app.core.exceptions import DeviceNotFoundError, InvalidSensorTypeError, ValidationError
from app.core.logging import logger

router = APIRouter(
    prefix="/api/v1/sensors",
    tags=["Sensor Readings"]
)

@router.post("/readings", response_model=SuccessResponse)
async def create_reading(
    reading: SensorReadingCreate,
    db: Session = Depends(get_db)
):
    """Create a new sensor reading"""
    try:
        service = SensorReadingService(db)
        result = service.process_reading(reading.dict())
        return SuccessResponse(
            success=True,
            message="Reading created successfully",
            data=result
        )
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidSensorTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating reading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/readings/batch", response_model=SuccessResponse)
async def create_readings_batch(
    batch: SensorReadingBatchCreate,
    db: Session = Depends(get_db)
):
    """Create multiple sensor readings"""
    try:
        service = SensorReadingService(db)
        results = []
        for reading in batch.readings:
            try:
                result = service.process_reading(reading.dict())
                results.append({"success": True, "reading": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "reading": reading.dict()})
        
        return SuccessResponse(
            success=True,
            message=f"Processed {len(results)} readings",
            data={
                "total": len(results),
                "successful": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"]),
                "results": results
            }
        )
    except Exception as e:
        logger.error(f"Error creating batch readings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/readings", response_model=PaginatedResponse)
async def get_readings(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    start_time: Optional[datetime] = Query(None, description="Start time (UTC)"),
    end_time: Optional[datetime] = Query(None, description="End time (UTC)"),
    limit: int = Query(100, ge=1, le=1000, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: Session = Depends(get_db)
):
    """Get sensor readings with filters"""
    try:
        service = SensorReadingService(db)
        result = service.get_readings(
            device_id=device_id,
            sensor_type=sensor_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        
        return PaginatedResponse(
            items=result["items"],
            total=result["total"],
            limit=result["limit"],
            offset=result["offset"],
            has_more=result["has_more"]
        )
    except Exception as e:
        logger.error(f"Error getting readings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/readings/latest", response_model=List[dict])
async def get_latest_readings_all(
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    db: Session = Depends(get_db)
):
    """Get latest reading for all devices"""
    try:
        service = SensorReadingService(db)
        if sensor_type:
            # Get latest readings by type
            readings = service.repository.get_latest_by_type(sensor_type)
            return [
                {
                    "device_id": r.device_id,
                    "sensor_type": r.sensor_type,
                    "value": float(r.value),
                    "unit": r.unit,
                    "time": r.time,
                    "quality": r.quality
                }
                for r in readings
            ]
        else:
            return service.get_latest_all_devices()
    except Exception as e:
        logger.error(f"Error getting latest readings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/readings/{device_id}/latest", response_model=dict)
async def get_latest_reading_by_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Get latest reading for a specific device"""
    try:
        service = SensorReadingService(db)
        result = service.get_latest_by_device(device_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Device {device_id} has no readings")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest reading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/readings/aggregated", response_model=List[SensorReadingAggregatedResponse])
async def get_aggregated_readings(
    sensor_type: str = Query(..., description="Sensor type"),
    time_bucket: str = Query("1 hour", description="Time bucket (e.g., 5 minutes, 1 hour, 1 day)"),
    start_time: datetime = Query(..., description="Start time (UTC)"),
    end_time: datetime = Query(..., description="End time (UTC)"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    db: Session = Depends(get_db)
):
    """Get aggregated sensor readings"""
    try:
        service = SensorReadingService(db)
        result = service.get_aggregated(
            sensor_type=sensor_type,
            time_bucket=time_bucket,
            start_time=start_time,
            end_time=end_time,
            device_id=device_id
        )
        return result
    except Exception as e:
        logger.error(f"Error getting aggregated readings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/readings/statistics", response_model=SensorReadingStatisticsResponse)
async def get_reading_statistics(
    sensor_type: str = Query(..., description="Sensor type"),
    start_time: datetime = Query(..., description="Start time (UTC)"),
    end_time: datetime = Query(..., description="End time (UTC)"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    db: Session = Depends(get_db)
):
    """Get statistics for sensor readings"""
    try:
        service = SensorReadingService(db)
        return service.get_statistics(
            sensor_type=sensor_type,
            start_time=start_time,
            end_time=end_time,
            device_id=device_id
        )
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/readings/anomalies", response_model=List[dict])
async def get_anomalies(
    sensor_type: str = Query(..., description="Sensor type"),
    threshold: float = Query(3.0, description="Z-score threshold"),
    start_time: Optional[datetime] = Query(None, description="Start time (UTC)"),
    end_time: Optional[datetime] = Query(None, description="End time (UTC)"),
    db: Session = Depends(get_db)
):
    """Detect anomalous readings"""
    try:
        service = SensorReadingService(db)
        return service.get_anomalies(
            sensor_type=sensor_type,
            threshold=threshold,
            start_time=start_time,
            end_time=end_time
        )
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))