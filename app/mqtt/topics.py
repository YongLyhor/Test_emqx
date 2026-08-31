from typing import Dict, List, Optional
from enum import Enum

class SensorType(str, Enum):
    """Sensor types enum"""
    WATER = "water"
    ELECTRICITY = "electricity"
    GAS = "gas"
    COOLING = "cooling"

class MQTTTopics:
    """MQTT topic definitions"""
    
    
    SENSOR_DATA = "sensor/{sensor_type}/{device_id}/data"
    SENSOR_STATUS = "sensor/{sensor_type}/{device_id}/status"
    SENSOR_CONFIG = "sensor/{sensor_type}/{device_id}/config"
    SENSOR_ALERT = "sensor/{sensor_type}/{device_id}/alert"
    
    
    ALL_SENSORS_DATA = "sensor/+/+/data"
    ALL_SENSORS_STATUS = "sensor/+/+/status"
    ALL_DEVICES_DATA = "sensor/+/+/data"
    SPECIFIC_TYPE_DATA = "sensor/{sensor_type}/+/data"
    
    @classmethod
    def get_data_topic(cls, sensor_type: str, device_id: str) -> str:
        """Get data topic for a specific sensor"""
        return cls.SENSOR_DATA.format(sensor_type=sensor_type, device_id=device_id)
    
    @classmethod
    def get_status_topic(cls, sensor_type: str, device_id: str) -> str:
        """Get status topic for a specific sensor"""
        return cls.SENSOR_STATUS.format(sensor_type=sensor_type, device_id=device_id)
    
    @classmethod
    def get_config_topic(cls, sensor_type: str, device_id: str) -> str:
        """Get config topic for a specific sensor"""
        return cls.SENSOR_CONFIG.format(sensor_type=sensor_type, device_id=device_id)
    
    @classmethod
    def get_type_data_topic(cls, sensor_type: str) -> str:
        """Get wildcard topic for all devices of a type"""
        return cls.SPECIFIC_TYPE_DATA.format(sensor_type=sensor_type)
    
    @classmethod
    def get_all_subscriptions(cls) -> List[str]:
        """Get all topics to subscribe to"""
        return [
            cls.ALL_SENSORS_DATA,
            cls.ALL_SENSORS_STATUS,
        ]
    
    @classmethod
    def parse_topic(cls, topic: str) -> Dict[str, str]:
        """Parse a topic string into components"""
        parts = topic.split('/')
        if len(parts) >= 4 and parts[0] == 'sensor':
            return {
                "sensor_type": parts[1],
                "device_id": parts[2],
                "message_type": parts[3] if len(parts) > 3 else "data"
            }
        return {}
    
    @classmethod
    def is_valid_topic(cls, topic: str) -> bool:
        """Check if topic is valid"""
        parsed = cls.parse_topic(topic)
        return (
            parsed.get("sensor_type") in [t.value for t in SensorType] and
            parsed.get("device_id") is not None
        )
    
    @classmethod
    def get_sensor_types(cls) -> List[str]:
        """Get all sensor types"""
        return [t.value for t in SensorType]