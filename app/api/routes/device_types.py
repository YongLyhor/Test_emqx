from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.service.device_type_service import DeviceTypeService
from app.schemas.request.device_type import DeviceTypeCreate, DeviceTypeUpdate
from app.schemas.response.device_type import DeviceTypeResponse, DeviceTypeDetailResponse
from app.schemas.response.common import SuccessResponse
from app.core.exceptions import RecordNotFoundError, ValidationError
from app.core.logging import logger

router = APIRouter(
    prefix="/api/v1/device-types",
    tags=["Device Types"]
)

@router.post("/", response_model=SuccessResponse)
async def create_device_type(
    device_type: DeviceTypeCreate,
    db: Session = Depends(get_db)
):
    """Create a new device type"""
    try:
        service = DeviceTypeService(db)
        result = service.create(**device_type.dict())
        return SuccessResponse(
            success=True,
            message="Device type created successfully",
            data=result
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating device type: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DeviceTypeResponse])
async def get_device_types(
    active_only: bool = Query(True, description="Only show active types"),
    db: Session = Depends(get_db)
):
    """Get all device types"""
    try:
        service = DeviceTypeService(db)
        if active_only:
            return service.get_active_types()
        else:
            return service.get_all()
    except Exception as e:
        logger.error(f"Error getting device types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{type_code}", response_model=DeviceTypeDetailResponse)
async def get_device_type(
    type_code: str,
    db: Session = Depends(get_db)
):
    """Get device type by code"""
    try:
        service = DeviceTypeService(db)
        result = service.get_by_code(type_code)
        return result["device_type"]
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting device type: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{type_code}", response_model=SuccessResponse)
async def update_device_type(
    type_code: str,
    device_type_update: DeviceTypeUpdate,
    db: Session = Depends(get_db)
):
    """Update a device type"""
    try:
        service = DeviceTypeService(db)
        device_type = service.get_by_code(type_code)
        if not device_type:
            raise HTTPException(status_code=404, detail=f"Device type {type_code} not found")
        
        updated = service.update(device_type["device_type"].id, **device_type_update.dict(exclude_unset=True))
        return SuccessResponse(
            success=True,
            message="Device type updated successfully",
            data=updated
        )
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating device type: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{type_code}", response_model=SuccessResponse)
async def delete_device_type(
    type_code: str,
    db: Session = Depends(get_db)
):
    """Delete a device type"""
    try:
        service = DeviceTypeService(db)
        device_type = service.get_by_code(type_code)
        if not device_type:
            raise HTTPException(status_code=404, detail=f"Device type {type_code} not found")
        
        service.delete(device_type["device_type"].id)
        return SuccessResponse(
            success=True,
            message=f"Device type {type_code} deleted successfully"
        )
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting device type: {e}")
        raise HTTPException(status_code=500, detail=str(e))