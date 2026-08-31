import json
import time
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import paho.mqtt.client as mqtt
from threading import Thread, Event
from app.core.config import settings
from app.core.logging import logger
from app.mqtt.topics import MQTTTopics

class MQTTClient:
   
    
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.connection_event = Event()
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.running = False
        self.thread: Optional[Thread] = None
        
       
        self.host = settings.MQTT_BROKER_HOST
        self.port = settings.MQTT_BROKER_PORT
        self.username = settings.MQTT_USERNAME
        self.password = settings.MQTT_PASSWORD
        self.client_id = settings.MQTT_CLIENT_ID
        self.keepalive = settings.MQTT_KEEPALIVE
        
       
        self.reconnect_delay = 5
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
    
    def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            
            self.client = mqtt.Client(
                client_id=self.client_id,
                protocol=mqtt.MQTTv5,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            
           
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish
            self.client.on_subscribe = self._on_subscribe
            
            
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
           
            self.client.enable_logger(logger)
            
            
            logger.info(f"Connecting to MQTT broker at {self.host}:{self.port}")
            self.client.connect(self.host, self.port, self.keepalive)
            
            
            self.running = True
            self.thread = Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            
           
            if self.connection_event.wait(timeout=10):
                logger.info("MQTT connection established successfully")
                return True
            else:
                logger.error("MQTT connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _run_loop(self) -> None:
        """Run the MQTT network loop"""
        while self.running:
            try:
                if self.client:
                    self.client.loop_forever()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in MQTT loop: {e}")
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    logger.info(f"Attempting reconnect {self.reconnect_attempts}/{self.max_reconnect_attempts}")
                    time.sleep(self.reconnect_delay * self.reconnect_attempts)
                    self.connect()
                else:
                    logger.error("Max reconnect attempts reached")
                    break
    
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback when connected to broker"""
        if reason_code == 0:
            self.connected = True
            self.reconnect_attempts = 0
            self.connection_event.set()
            logger.info(f"Connected to MQTT broker with result code {reason_code}")
            
            # Subscribe to topics
            self._subscribe_to_topics()
        else:
            logger.error(f"Failed to connect to MQTT broker with reason code {reason_code}")
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Callback when disconnected from broker"""
        self.connected = False
        self.connection_event.clear()
        logger.warning(f"Disconnected from MQTT broker with reason code {reason_code}")
    
    def _on_message(self, client, userdata, message):
        """Callback when message is received"""
        try:
            topic = message.topic
            payload = message.payload.decode('utf-8')
            qos = message.qos
            
            logger.debug(f"Received message on topic: {topic}, QoS: {qos}")
            
            # Parse message
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON payload on topic {topic}: {payload}")
                return
            
            # Process message
            self._process_message(topic, data, qos)
            
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _on_publish(self, client, userdata, mid, reason_code, properties):
        """Callback when message is published"""
        logger.debug(f"Message published with mid: {mid}, reason_code: {reason_code}")
    
    def _on_subscribe(self, client, userdata, mid, reason_codes, properties):
        """Callback when subscribed to topic"""
        logger.info(f"Subscribed with mid: {mid}, reason_codes: {reason_codes}")
    
    def _subscribe_to_topics(self) -> None:
        """Subscribe to all required topics"""
        try:
            topics = MQTTTopics.get_all_subscriptions()
            for topic in topics:
                result = self.client.subscribe(topic, qos=1)
                logger.info(f"Subscribed to topic: {topic}, result: {result}")
        except Exception as e:
            logger.error(f"Error subscribing to topics: {e}")
    
    def _process_message(self, topic: str, data: Dict[str, Any], qos: int) -> None:
        """Process incoming MQTT message"""
        # Parse topic
        parsed = MQTTTopics.parse_topic(topic)
        if not parsed:
            logger.warning(f"Could not parse topic: {topic}")
            return
        
        # Add topic info to data
        data['_topic'] = topic
        data['_sensor_type'] = parsed.get('sensor_type')
        data['_device_id'] = parsed.get('device_id')
        data['_message_type'] = parsed.get('message_type', 'data')
        data['_qos'] = qos
        
        
        message_type = data['_message_type']
        if message_type in self.message_handlers:
            for handler in self.message_handlers[message_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in message handler for {message_type}: {e}")
        
        
        if message_type != 'data' and 'data' in self.message_handlers:
            for handler in self.message_handlers['data']:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in data handler: {e}")
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a message handler"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        logger.info(f"Registered handler for message type: {message_type}")
    
    def unregister_handler(self, message_type: str, handler: Callable) -> None:
        """Unregister a message handler"""
        if message_type in self.message_handlers:
            try:
                self.message_handlers[message_type].remove(handler)
                logger.info(f"Unregistered handler for message type: {message_type}")
            except ValueError:
                pass
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1, retain: bool = False) -> bool:
        """Publish a message to a topic"""
        try:
            if not self.connected or not self.client:
                logger.error("MQTT client not connected")
                return False
            
            message = json.dumps(payload)
            result = self.client.publish(topic, message, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {payload}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
            return False
    
    def publish_sensor_data(self, sensor_type: str, device_id: str, data: Dict[str, Any]) -> bool:
        """Publish sensor data"""
        topic = MQTTTopics.get_data_topic(sensor_type, device_id)
        return self.publish(topic, data)
    
    def subscribe(self, topic: str, qos: int = 1) -> bool:
        """Subscribe to a topic"""
        try:
            if not self.connected or not self.client:
                logger.error("MQTT client not connected")
                return False
            
            result = self.client.subscribe(topic, qos=qos)
            logger.info(f"Subscribed to {topic} with QoS {qos}")
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error(f"Error subscribing to {topic}: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MQTT broker"""
        self.running = False
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
            self.connected = False
            logger.info("Disconnected from MQTT broker")
    
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self.connected and self.client is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get MQTT client status"""
        return {
            "connected": self.is_connected(),
            "host": self.host,
            "port": self.port,
            "client_id": self.client_id,
            "reconnect_attempts": self.reconnect_attempts,
            "handlers_count": sum(len(h) for h in self.message_handlers.values())
        }