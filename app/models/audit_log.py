from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.sql import func
from app.models import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(String(100), nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)
    old_data = Column(JSONB)
    new_data = Column(JSONB)
    performed_by = Column(String(100))
    ip_address = Column(INET)
    created_at = Column(DateTime(timezone=True), server_default=func.now())