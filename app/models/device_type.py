from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime
from sqlalchemy.sql import func
from app.models import Base

class DeviceType(Base):
    __tablename__ = 'device_types'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_code = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    default_unit = Column(String(20), nullable=False)
    min_value = Column(Numeric(15, 6))
    max_value = Column(Numeric(15, 6))
    alert_threshold = Column(Numeric(15, 6))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())