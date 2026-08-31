from sqlalchemy import Column, String, DateTime, Integer, Date, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.models import Base
import uuid

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    sensor_type = Column(String(50), nullable=False, index=True)
    location = Column(String(200))
    building = Column(String(100))
    floor = Column(Integer)
    room = Column(String(50))
    installation_date = Column(Date)
    firmware_version = Column(String(20))
    status = Column(String(20), default='active', index=True)
    metadata_ = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())