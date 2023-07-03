
import datetime
import json
import logging as log
import signal
import sys
import os
import time
import traceback
from mongita import MongitaClientDisk
from mongita.database import Database
from mongita.collection import Collection
from bson import ObjectId, InvalidBSON

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

class DatabaseService():
    def __init__(self, db_name: str) -> None:
        self.name = db_name
        self._db_client = MongitaClientDisk(".mongita")
        self._db: Database = eval(f"self._db_client.{db_name}")
        self._stop = False
        signal.signal(signal.SIGINT, self._handle_termination)
        signal.signal(signal.SIGTERM, self._handle_termination)
    def _handle_termination(self, signum, frame):
        log.info("Termination signal received. Stopping gracefully...")
        self._stop = True

    def insert_data(self, coll_name: str, data: dict):
 #       coll: Collection = eval(f"self._db.{coll_name}")
 #       try:
 #           log.debug(f"{coll_name}: {data}")
 #           coll.insert_one(data)
 #       except InvalidBSON as ibe:
 #           log.warning("probleme archivage:{coll_name}, data:{data}, passage au suivant")
    
 # Check if the file exists
        if self._stop:
            log.info("Insert data operation stopped.")
            return
        if not os.path.isfile('/home/pi/MothHub/data1.json'):
        # Create the file and write the first entry
            with open('/home/pi/MothHub/data1.json', 'w+') as f:
                json.dump([data], f, indent=4)
                f.flush()
                os.fsync(f.fileno())
        else:
            # Read the existing data
            with open('/home/pi/MothHub/data1.json', 'r') as f:
                file_data = json.load(f)
                if not isinstance(file_data, list):
                    file_data =[file_data]

            # Append the new data
            file_data.append(data)
            
            # Write the updated data back to the file
            with open('/home/pi/MothHub/data1.json', 'w+') as f:
                json.dump(file_data, f, indent=4)  
                f.flush()
                os.fsync(f.fileno()) 
    
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
    def __init__(self, name: str, mqtt_broker: str = "localhost", mqtt_broker_port: int = 1883) -> None:
        super().__init__([MqttTopics.ALL], mqtt_broker, mqtt_broker_port)
        self.db_srv = DatabaseService(name)

        # Setup gracefull exit on kill        
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        # Exceptionaly overwriting the on_message method of the mqtt client because we want it called on ANY topic.
        self.mqtt_clients[MqttTopics.ALL].client.on_message = self.on_message

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        log.debug(f"Recieved: [{msg.topic}]:{msg.payload}\n")
        payload = json.loads(msg.payload)
        self.db_srv.insert_data(msg.topic, payload)

    def exit_gracefully(self):
        print('Shutting down gracefully...')
        sys.exit(0)


class Database(MonginaDatabaseModule): pass

if __name__ == "__main__":
    log.basicConfig(level=log.DEBUG)
    db = Database("rafale3_local_archive")

    while True:
        time.sleep(0.1)
