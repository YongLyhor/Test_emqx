from typing import Dict, Any, Optional
from app.core.logging import logger
from app.mqtt.client import MQTTClient
from app.mqtt.topics import MQTTTopics
from datetime import datetime

class MQTTPublisher:
    """MQTT publisher for sending commands and configuration"""

    def __init__(self, mqtt_client: MQTTClient):
        self.client = mqtt_client
    
    def publish_command(
        self,
        sensor_type: str,
        device_id: str,
        command: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Publish a command to a device"""
        try:
            topic = f"sensor/{sensor_type}/{device_id}/command"
            payload = {
                "command": command,
                "data": data or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return self.client.publish(topic, payload, qos=1)
            
        except Exception as e:
            logger.error(f"Error publishing command to {device_id}: {e}")
            return False
    
    def publish_config_update(
        self,
        sensor_type: str,
        device_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """Publish configuration update to a device"""
        try:
            topic = MQTTTopics.get_config_topic(sensor_type, device_id)
            payload = {
                "config": config,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return self.client.publish(topic, payload, qos=1, retain=True)
            
        except Exception as e:
            logger.error(f"Error publishing config to {device_id}: {e}")
            return False
    
    def publish_status_request(self, sensor_type: str, device_id: str) -> bool:
        """Request status from a device"""
        try:
            topic = f"sensor/{sensor_type}/{device_id}/request"
            payload = {
                "request": "status",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return self.client.publish(topic, payload, qos=1)
            
        except Exception as e:
            logger.error(f"Error requesting status from {device_id}: {e}")
            return False