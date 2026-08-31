from typing import Optional, Any
from fastapi import HTTPException, status

class BaseAppException(Exception):
    """Base exception for application"""
    def __init__(self, message: str, status_code: int = 400, details: Optional[Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)

# Database Exceptions
class DatabaseError(BaseAppException):
    def __init__(self, message: str = "Database error occurred", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)

class RecordNotFoundError(BaseAppException):
    def __init__(self, record_type: str, record_id: str):
        super().__init__(
            message=f"{record_type} with id '{record_id}' not found",
            status_code=404
        )

# MQTT Exceptions
class MQTTConnectionError(BaseAppException):
    def __init__(self, message: str = "Failed to connect to MQTT broker"):
        super().__init__(message, status_code=503)

class MQTTSubscriptionError(BaseAppException):
    def __init__(self, topic: str, message: str = "Failed to subscribe to topic"):
        super().__init__(f"{message}: {topic}", status_code=500)

# Device Exceptions
class DeviceNotFoundError(BaseAppException):
    def __init__(self, device_id: str):
        super().__init__(
            message=f"Device '{device_id}' not found",
            status_code=404
        )

class DeviceAlreadyExistsError(BaseAppException):
    def __init__(self, device_id: str):
        super().__init__(
            message=f"Device '{device_id}' already exists",
            status_code=409
        )

class InvalidSensorTypeError(BaseAppException):
    def __init__(self, sensor_type: str):
        super().__init__(
            message=f"Invalid sensor type '{sensor_type}'",
            status_code=400
        )

# Sensor Reading Exceptions
class InvalidReadingError(BaseAppException):
    def __init__(self, message: str = "Invalid sensor reading data"):
        super().__init__(message, status_code=400)

class ReadingOutOfRangeError(BaseAppException):
    def __init__(self, value: float, min_val: float, max_val: float):
        super().__init__(
            message=f"Value {value} out of range ({min_val} - {max_val})",
            status_code=400
        )

# Authentication Exceptions (Future)
class AuthenticationError(BaseAppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class AuthorizationError(BaseAppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)

# Validation Exception
class ValidationError(BaseAppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, status_code=422, details=details)

# FastAPI HTTP Exception Mapper
def to_http_exception(exc: BaseAppException) -> HTTPException:
    """Convert custom exception to FastAPI HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "details": exc.details
        }
    )