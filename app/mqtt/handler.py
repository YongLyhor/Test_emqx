from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.service.sensor_reading_service import SensorReadingService
from app.service.device_service import DeviceService
from app.service.alert_service import AlertService
from app.service.device_type_service import DeviceTypeService

class MQTTMessageHandler:
    """Handler for processing MQTT messages"""
    
    def __init__(self, db: Session):
        self.db = db
        self.reading_service = SensorReadingService(db)
        self.device_service = DeviceService(db)
        self.alert_service = AlertService(db)
        self.device_type_service = DeviceTypeService(db)
        
        # Initialize handlers
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register message handlers with MQTT client"""
        # This will be called from the main app after MQTT client is initialized
        pass
    
    def handle_data_message(self, data: Dict[str, Any]) -> None:
        """Handle sensor data message"""
        try:
            logger.info(f"Processing sensor data: {data.get('_device_id')}")
            
            # Extract data
            sensor_type = data.get('_sensor_type')
            device_id = data.get('_device_id')
            
            if not sensor_type or not device_id:
                logger.error("Missing sensor_type or device_id in message")
                return
            
            # Prepare reading data
            reading_data = {
                "sensor_type": sensor_type,
                "device_id": device_id,
                "time": data.get('time', datetime.utcnow()),
                "value": data.get('value'),
                "unit": data.get('unit'),
                "quality": data.get('quality', 100),
                "metadata": data.get('metadata', {})
            }
            
            # Validate required fields
            if reading_data["value"] is None:
                logger.error(f"Missing value in message from {device_id}")
                return
            
            if not reading_data["unit"]:
                logger.error(f"Missing unit in message from {device_id}")
                return
            
            # Process reading
            result = self.reading_service.process_reading(reading_data)
            
            logger.info(f"Processed reading for device {device_id}: {result}")
            
        except Exception as e:
            logger.error(f"Error handling data message: {e}")
    
    def handle_status_message(self, data: Dict[str, Any]) -> None:
        """Handle sensor status message"""
        try:
            device_id = data.get('_device_id')
            sensor_type = data.get('_sensor_type')
            
            if not device_id:
                logger.error("Missing device_id in status message")
                return
            
            status = data.get('status')
            if not status:
                logger.error("Missing status in status message")
                return
            
            # Update device status
            self.device_service.update_device_status(device_id, status)
            
            # Create alert if status is critical
            if status == 'inactive' or status == 'maintenance':
                self.alert_service.create_alert({
                    "device_id": device_id,
                    "sensor_type": sensor_type or 'unknown',
                    "alert_type": "status_change",
                    "severity": "warning" if status == 'maintenance' else "critical",
                    "message": f"Device {device_id} status changed to {status}",
                    "value": None,
                    "threshold_value": None
                })
            
            logger.info(f"Updated status for device {device_id}: {status}")
            
        except Exception as e:
            logger.error(f"Error handling status message: {e}")
    
    def handle_config_message(self, data: Dict[str, Any]) -> None:
        """Handle sensor config message"""
        try:
            device_id = data.get('_device_id')
            
            if not device_id:
                logger.error("Missing device_id in config message")
                return
            
            # Update device configuration
            config_data = {
                "firmware_version": data.get('firmware_version'),
                "metadata": data.get('metadata', {})
            }
            
            # Remove None values
            config_data = {k: v for k, v in config_data.items() if v is not None}
            
            if config_data:
                self.device_service.update_device(device_id, config_data)
                logger.info(f"Updated config for device {device_id}: {config_data}")
            
        except Exception as e:
            logger.error(f"Error handling config message: {e}")
    
    def handle_alert_message(self, data: Dict[str, Any]) -> None:
        """Handle sensor alert message"""
        try:
            device_id = data.get('_device_id')
            sensor_type = data.get('_sensor_type')
            
            if not device_id:
                logger.error("Missing device_id in alert message")
                return
            
            # Create alert
            alert_data = {
                "device_id": device_id,
                "sensor_type": sensor_type or 'unknown',
                "alert_type": data.get('alert_type', 'sensor_alert'),
                "severity": data.get('severity', 'warning'),
                "message": data.get('message', 'Sensor alert'),
                "value": data.get('value'),
                "threshold_value": data.get('threshold_value')
            }
            
            self.alert_service.create_alert(alert_data)
            logger.info(f"Created alert for device {device_id}: {alert_data['alert_type']}")
            
        except Exception as e:
            logger.error(f"Error handling alert message: {e}")
    
    def get_handler_for_type(self, message_type: str):
        """Get handler function for message type"""
        handlers = {
            'data': self.handle_data_message,
            'status': self.handle_status_message,
            'config': self.handle_config_message,
            'alert': self.handle_alert_message
        }
        return handlers.get(message_type)