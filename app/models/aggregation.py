from sqlalchemy import Column, BigInteger, String, DateTime, Numeric, Integer
from sqlalchemy.sql import func
from app.models import Base

class DataAggregation(Base):
    __tablename__ = 'data_aggregations'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sensor_type = Column(String(50), nullable=False)
    device_id = Column(String(100), index=True)
    time_bucket = Column(DateTime(timezone=True), nullable=False)
    period = Column(String(20), nullable=False, index=True)
    avg_value = Column(Numeric(15, 6))
    max_value = Column(Numeric(15, 6))
    min_value = Column(Numeric(15, 6))
    count = Column(Integer)
    sum_value = Column(Numeric(15, 6))
    created_at = Column(DateTime(timezone=True), server_default=func.now())