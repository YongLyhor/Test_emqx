from sqlalchemy import Column, BigInteger, String, DateTime, Numeric, Boolean, Text
from sqlalchemy.sql import func
from app.models import Base

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(String(100), nullable=False, index=True)
    sensor_type = Column(String(50), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    value = Column(Numeric(15, 6))
    threshold_value = Column(Numeric(15, 6))
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())