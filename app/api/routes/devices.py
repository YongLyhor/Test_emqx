from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.service.device_service import DeviceService
from app.schemas.request.device import DeviceCreate, DeviceUpdate, DeviceQueryParams
from app.schemas.response.device import DeviceResponse, DeviceDetailResponse, DeviceWithStatsResponse
from app.schemas.response.common import PaginatedResponse, SuccessResponse
from app.core.exceptions import (
    DeviceNotFoundError,
    DeviceAlreadyExistsError,
    InvalidSensorTypeError,
    ValidationError
)
from app.core.logging import logger

router = APIRouter(
    prefix="/api/v1/devices",
    tags=["Devices"]
)

@router.post("/", response_model=SuccessResponse)
async def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db)
):
    """Create a new device"""
    try:
        service = DeviceService(db)
        result = service.create_device(device.dict())
        return SuccessResponse(
            success=True,
            message="Device created successfully",
            data=result
        )
    except DeviceAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidSensorTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=PaginatedResponse)
async def get_devices(
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    building: Optional[str] = Query(None, description="Filter by building"),
    search: Optional[str] = Query(None, description="Search by name or device_id"),
    limit: int = Query(100, ge=1, le=1000, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: Session = Depends(get_db)
):
    """Get all devices with filters"""
    try:
        service = DeviceService(db)
        result = service.get_devices(
            sensor_type=sensor_type,
            status=status,
            building=building,
            search=search,
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
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active", response_model=List[dict])
async def get_active_devices(
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    db: Session = Depends(get_db)
):
    """Get all active devices"""
    try:
        service = DeviceService(db)
        return service.get_active_devices(sensor_type)
    except Exception as e:
        logger.error(f"Error getting active devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{device_id}", response_model=DeviceDetailResponse)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Get device by device_id"""
    try:
        service = DeviceService(db)
        result = service.get_device(device_id)
        return result["device"]
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{device_id}/stats", response_model=DeviceWithStatsResponse)
async def get_device_with_stats(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Get device with statistics"""
    try:
        service = DeviceService(db)
        result = service.get_device_with_stats(device_id)
        return result
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting device stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{device_id}", response_model=SuccessResponse)
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db)
):
    """Update a device"""
    try:
        service = DeviceService(db)
        result = service.update_device(device_id, device_update.dict(exclude_unset=True))
        return SuccessResponse(
            success=True,
            message="Device updated successfully",
            data=result
        )
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidSensorTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{device_id}/status", response_model=SuccessResponse)
async def update_device_status(
    device_id: str,
    status: str = Query(..., description="Status: active, inactive, maintenance"),
    db: Session = Depends(get_db)
):
    """Update device status"""
    try:
        service = DeviceService(db)
        result = service.update_device_status(device_id, status)
        return SuccessResponse(
            success=True,
            message=f"Device status updated to {status}",
            data=result
        )
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating device status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{device_id}", response_model=SuccessResponse)
async def delete_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Delete a device"""
    try:
        service = DeviceService(db)
        result = service.delete_device(device_id)
        return SuccessResponse(
            success=True,
            message=result["message"]
        )
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        raise HTTPException(status_code=500, detail=str(e))