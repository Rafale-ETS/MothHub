
import datetime
import json
import logging as log
import signal
import sys
from time import sleep
from mongita import MongitaClientDisk
from mongita.database import Database
from mongita.collection import Collection
from bson import ObjectId

import paho.mqtt.client as mqtt

import requests

from modules.mqtt_utils import MqttTopics
from .mqtt_modules import MqttSubModule

# Handle races as object of data points
# Be able to load only race metadata (start/end time, etc) without loading data points

# Database structure:
# - [database] rafale3
#   - [collection] races
#     - [document] race 1 #TODO: define the race data structure and when we save it.
#   - [collection] speed
#     - [document] mqtt speed packet (one document per packet recieved)
#   - [collection] position
#     - [document] mqtt position packet (one document per packet recieved)
#   - ... (one collection per mqtt topic + races)
#     - ... (one document per related mqtt packet recieved)

DB_BASE_URL = "http://christobrary.net:30800/rafale/data"
DB_LAST_TMSTMP = "latest"
CONTENT_TYPE = 'Content-Type: application/json'

class RemoteArchiver(MqttSubModule):
    def __init__(self, mqtt_broker: str = "localhost", mqtt_broker_port: int = 1883) -> None:
        super().__init__([MqttTopics.ALL], mqtt_broker, mqtt_broker_port, False)

        # Setup gracefull exit on kill        
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        # Exceptionaly overwriting the on_message method of the mqtt client because we want it called on ANY topic.
        self.mqtt_clients[MqttTopics.ALL].client.on_message = self.on_message

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        log.debug(f"Recieved: [{msg.topic}]:{msg.payload}\n")
        payload = json.loads(msg.payload)

        # send data to the database, ided by timestamps
        requests.post(f"{DB_BASE_URL}/{msg.topic}/{payload['time']}", json=payload, headers=CONTENT_TYPE)
        requests.post(f"{DB_BASE_URL}/{msg.topic}/{DB_LAST_TMSTMP}",  json=payload, headers=CONTENT_TYPE)

    def exit_gracefully(self, a, b):
        log.info("Quiting remote archiver.")
        sys.exit(0)

    def run(self):
        log.info("Starting mqtt client.")
        #self.mqtt_clients[MqttTopics.ALL].client.loop_start()
        while(True):
            print(".")
            self.mqtt_clients[MqttTopics.ALL].client.loop()
            #sleep(0.01)

#log.basicConfig(level=log.INFO)
log.info("Starting remote archiver...")
remArch = RemoteArchiver()
log.info("Archiver running.")
remArch.run()
log.info("After run... ")
