from sqlalchemy.orm import Session
from app.core.logging import logger
from app.mqtt.client import MQTTClient
from app.mqtt.handler import MQTTMessageHandler
from app.mqtt.topics import MQTTTopics
from typing import Optional

class MQTTInitializer:
    """Initialize MQTT connections and handlers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = None
        self.handler = None
    
    def initialize(self) -> bool:
        """Initialize MQTT client and handlers"""
        try:
            # Create client
            self.client = MQTTClient()
            
            # Create handler
            self.handler = MQTTMessageHandler(self.db)
            
            # Register handlers with client
            self._register_handlers()
            
            # Connect to broker
            if not self.client.connect():
                logger.error("Failed to connect to MQTT broker")
                return False
            
            logger.info("MQTT initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MQTT: {e}")
            return False
    
    def _register_handlers(self) -> None:
        """Register message handlers with client"""
        # Register data handler
        self.client.register_handler('data', self.handler.handle_data_message)
        
        # Register status handler
        self.client.register_handler('status', self.handler.handle_status_message)
        
        # Register config handler
        self.client.register_handler('config', self.handler.handle_config_message)
        
        # Register alert handler
        self.client.register_handler('alert', self.handler.handle_alert_message)
        
        logger.info("Registered MQTT message handlers")
    
    def get_client(self) -> Optional[MQTTClient]:
        """Get MQTT client instance"""
        return self.client
    
    def get_handler(self) -> Optional[MQTTMessageHandler]:
        """Get MQTT handler instance"""
        return self.handler
    
    def shutdown(self) -> None:
        """Shutdown MQTT connections"""
        if self.client:
            self.client.disconnect()
            logger.info("MQTT shutdown complete")