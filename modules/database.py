

import datetime
import json
import logging as log
import signal
import sys
import time
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

class DatabaseService():
    def __init__(self, db_name: str) -> None:
        self.name = db_name
        self._db_client = MongitaClientDisk(".mongita")
        self._db: Database = eval(f"self._db_client.{db_name}")

    def insert_data(self, coll_name: str, data: dict):
        coll: Collection = eval(f"self._db.{coll_name}")
        coll.insert_one(data)

    # from_date has to be further in time than to_date. Ex: from 25/02/2022 to 30/02/2022
    # Defaults to data up to this instant if only from is provided.
    def obtain_data_from_date(self, coll_name: str, from_date: datetime.datetime, to_date: datetime.datetime = datetime.datetime.now()):
        from_id = ObjectId.from_datetime(from_date.astimezone(datetime.timezone.utc))
        to_id = ObjectId.from_datetime(to_date.astimezone(datetime.timezone.utc))
        time_range_filter = {
            "_id": {
                "$gt": from_id,
                "$lte": to_id
            }
        }
        coll: Collection = eval(f"self._db.{coll_name}")
        return list(coll.find(time_range_filter))

class MonginaDatabaseModule(MqttSubModule):
    def __init__(self, mqtt_broker: str = "localhost", mqtt_broker_port: int = 1883) -> None:

        log.warning("THIS IS A DEPRECATED VERSION OF THE DATABASE, DO NOT USE!")

        super().__init__([MqttTopics.ALL], mqtt_broker, mqtt_broker_port)
        self.db_srv = DatabaseService("rafale3")

        # Setup gracefull exit on kill
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        # Exceptionaly overwriting the on_message method of the mqtt client because we want it called on ANY topic.
        self.mqtt_clients[MqttTopics.ALL].client.on_message = self.on_message

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        log.debug(f"Recieved: [{msg.topic}]:{msg.payload}\n")
        payload = json.loads(msg.payload)
        self.db_srv.insert_data(msg.topic, payload)

        # send data to the database, ided by timestamps
        requests.post(f"{DB_BASE_URL}/{msg.topic}/{payload['time']}", json=payload, headers=CONTENT_TYPE)
        requests.post(f"{DB_BASE_URL}/{msg.topic}/{DB_LAST_TMSTMP}",  json=payload, headers=CONTENT_TYPE)

    def exit_gracefully(self):
        self.db_srv._db_client.close()
        sys.exit(0)

class Database(MonginaDatabaseModule): pass

log.basicConfig(level=log.INFO)
db = Database()

while True:
    time.sleep(0.1)
