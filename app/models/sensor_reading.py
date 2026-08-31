from sqlalchemy import Column, BigInteger, String, DateTime, Numeric, Integer, JSON, Identity, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models import Base

class SensorReading(Base):
    __tablename__ = 'sensor_readings'
    __table_args__ = (PrimaryKeyConstraint('time', 'id'),)
    
    id = Column(BigInteger, Identity(), nullable=False)
    time = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sensor_type = Column(String(50), nullable=False)
    device_id = Column(String(100), nullable=False)
    value = Column(Numeric(15, 6), nullable=False)
    unit = Column(String(20), nullable=False)
    quality = Column(Integer, default=100)
    metadata_ = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())