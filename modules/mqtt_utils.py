import logging as log
from dataclasses import dataclass
import paho.mqtt.client as mqtt

DEFAULT_BROKER = "localhost"
DEFAULT_PORT = 1883

@dataclass
class MqttTopics:
    ALL = "#"
    SPEED = "speed" # GPS/IMU speed
    DIRECTION = "direction" # (Heading) GPS
    ORIENTATION = "orientation" # IMU
    POSITION = "position" # GPS
    WIND = "wind_data"
   
    STRENGHT = "strength" # Strength/tension gages
    STATUS = "status" # errors and reporting

class MqttPubClient:
    def __init__(self, mqtt_topic: str, mqtt_broker: str = DEFAULT_BROKER, mqtt_broker_port: int = DEFAULT_PORT) -> None:
        self.mqtt_topic = mqtt_topic
        
        self.client = mqtt.Client()
        
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish

        self.client.connect(mqtt_broker, mqtt_broker_port, 60)
        
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client: mqtt.Client, userdata, flags, rc):
        log.info(f"Mqtt pub client for {self.mqtt_topic} connected with result code {rc}\n")

    def on_publish(self, client: mqtt.Client, userdata, result):
        #log.debug(f"Published with result: {result}.")
        pass
    
    def publish(self, message):
        ret = self.client.publish(self.mqtt_topic, message)
        log.debug(f"Published: [{self.mqtt_topic}]:{message}->{ret}\n")

class MqttSubClient:
    def __init__(self, mqtt_topic: str, mqtt_broker: str = DEFAULT_BROKER, mqtt_broker_port = DEFAULT_PORT, start=True) -> None:
        self.mqtt_topic = mqtt_topic
        
        self.client = mqtt.Client()
        self.message_callback_add = self.client.message_callback_add

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect_async(mqtt_broker, mqtt_broker_port, 60)
        if start:
            self.client.loop_start()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client: mqtt.Client, userdata, flags, rc):
        log.info(f"Mqtt sub client for {self.mqtt_topic} connected with result code {rc}\n")

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.mqtt_topic)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        log.debug(f"Recieved: [{msg.topic}]:{msg.payload}\n")

    def __del__(self):
        self.client.loop_stop()
