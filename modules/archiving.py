import signal
import sys
import json
import requests
import time
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
#archivage externe d'un ancien (Christo) actuellement non fonctionnel
import logging as log
import paho.mqtt.client as mqtt

from .mqtt_utils import MqttTopics
from .mqtt_modules import MqttSubModule
from .data_models.mqtt_packets import MQTTPacket

API_URL = "https://n4pc4r.deta.dev"
END_RACES = "/race"
def END_RACE(id): return f"{END_RACE}/{id}"
def END_DATA(race_id, data_id): return f"{END_RACE}/{race_id}/{data_id}"
def API(end): return f"{API_URL}{end}"

DEFAULT_CURRENT_RACE_RANGE = 60 #seconds any race last modified earlier than this is considered finished, on system start.

@dataclass
class ArchivePacket:
    last_status: str = "unsent"
    #TODO: actually format this to host all packets
    data: "dict(str,list)" = field(default_factory=lambda: {})

def send_task(module):
    while(not module.stop):
        #TODO: format data
        #TODO: send data
        #requests.post()
        time.sleep(1) # Send data every second

#TODO: proper error handling
def get_current_race(range_sec: int = DEFAULT_CURRENT_RACE_RANGE, force_new = False):
    if not force_new:
        resp = requests.get(API(END_RACES))
        if resp.status_code == 200:
            data = resp.json()

            curr_race = {"last_mod": 0} # Faking a race dict
            max_tmstmp = (datetime.utcnow() - timedelta(seconds=range_sec)).timestamp()

            for race in data:
                #TODO: Check for proper timestamp
                if (race["last_mod"] > max_tmstmp) and (curr_race["last_mod"] < race["last_mod"]):
                    curr_race = race

            if curr_race["last_mod"] > 0:
                return curr_race["key"]

    # else either we want a new race, or haven't found a current one
    now = datetime.utcnow().timestamp()
    data = {
        "timestamp": now,
        "last_mod": now,
        #TODO: make a nice template
    }
    resp = requests.post(API(END_RACES), json=json.dumps(data))
    if resp.status_code == 200:
        return resp.json()["key"]

class ArchivingMQTTModule(MqttSubModule):
    def __init__(self, mqtt_broker: str = "localhost", mqtt_broker_port: int = 1883) -> None:
        super().__init__([MqttTopics.ALL], mqtt_broker, mqtt_broker_port)

        self.packet_queue: 'deque(ArchivePacket)' = deque()
        self.current_packet: ArchivePacket = ArchivePacket()

        # Setup gracefull exit on kill
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        # Exceptionaly overwriting the on_message method of the mqtt client because we want it called on ANY topic.
        self.mqtt_clients[MqttTopics.ALL].client.on_message = self.on_message
        self.stop = False
        self.sending: asyncio.Task = asyncio.create_task(send_task(self))

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        log.debug(f"Recieved: [{msg.topic}]:{msg.payload}\n")
        pkt = MQTTPacket.from_payload(msg.payload)
        self.current_packet.data[pkt.type].append(pkt)

    def _format_data(new_data: dict):
        return 0

    def exit_gracefully(self):
        self.stop = True
        self.sending.cancel()
        sys.exit(0)

#log.basicConfig(level=log.INFO)
log.basicConfig(level=log.DEBUG)
archiving = ArchivingMQTTModule()
#TODO: make a better way to sleep and let the rest work.
while True:
    time.sleep(0.1)
