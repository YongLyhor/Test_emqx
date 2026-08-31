from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.service.alert_service import AlertService
from app.schemas.request.alert import AlertCreate, AlertResolveRequest, AlertQueryParams
from app.schemas.response.alert import AlertResponse, AlertDetailResponse
from app.schemas.response.common import PaginatedResponse, SuccessResponse
from app.core.exceptions import RecordNotFoundError, ValidationError
from app.core.logging import logger

router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["Alerts"]
)

@router.post("/", response_model=SuccessResponse)
async def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db)
):
    """Create a new alert"""
    try:
        service = AlertService(db)
        result = service.create_alert(alert.dict())
        return SuccessResponse(
            success=True,
            message="Alert created successfully",
            data=result
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=PaginatedResponse)
async def get_alerts(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    start_time: Optional[datetime] = Query(None, description="Start time (UTC)"),
    end_time: Optional[datetime] = Query(None, description="End time (UTC)"),
    limit: int = Query(100, ge=1, le=1000, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: Session = Depends(get_db)
):
    """Get all alerts with filters"""
    try:
        service = AlertService(db)
        result = service.get_alerts(
            device_id=device_id,
            sensor_type=sensor_type,
            severity=severity,
            resolved=resolved,
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
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unresolved", response_model=List[dict])
async def get_unresolved_alerts(
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    db: Session = Depends(get_db)
):
    """Get all unresolved alerts"""
    try:
        service = AlertService(db)
        return service.get_unresolved_alerts(sensor_type)
    except Exception as e:
        logger.error(f"Error getting unresolved alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=dict)
async def get_alert_stats(
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    start_time: Optional[datetime] = Query(None, description="Start time (UTC)"),
    end_time: Optional[datetime] = Query(None, description="End time (UTC)"),
    db: Session = Depends(get_db)
):
    """Get alert statistics"""
    try:
        service = AlertService(db)
        return service.get_alert_stats(sensor_type, start_time, end_time)
    except Exception as e:
        logger.error(f"Error getting alert stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{alert_id}/resolve", response_model=SuccessResponse)
async def resolve_alert(
    alert_id: int,
    resolve_request: Optional[AlertResolveRequest] = None,
    db: Session = Depends(get_db)
):
    """Resolve an alert"""
    try:
        service = AlertService(db)
        resolved_at = resolve_request.resolved_at if resolve_request else None
        result = service.resolve_alert(alert_id, resolved_at)
        return SuccessResponse(
            success=True,
            message="Alert resolved successfully",
            data=result
        )
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))