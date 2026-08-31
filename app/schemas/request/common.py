from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PaginationParams(BaseModel):
    """Common pagination parameters"""
    limit: int = Field(100, description="Number of results per page", ge=1, le=1000)
    offset: int = Field(0, description="Number of results to skip", ge=0)
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field('desc', description="Sort order: asc, desc")
    
    class Config:
        json_schema_extra = {
            "example": {
                "limit": 50,
                "offset": 0,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }

class DateRangeParams(BaseModel):
    """Common date range parameters"""
    start_time: Optional[datetime] = Field(None, description="Start time (UTC)")
    end_time: Optional[datetime] = Field(None, description="End time (UTC)")
    timezone: Optional[str] = Field('UTC', description="Timezone for display")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_time": "2026-08-26T00:00:00Z",
                "end_time": "2026-08-27T00:00:00Z",
                "timezone": "UTC"
            }
        }