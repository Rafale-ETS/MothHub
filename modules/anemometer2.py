#anemometer python code
import asyncio
import datetime
import logging as log
import signal

from calypso_anemometer.core import CalypsoDeviceApi, Settings
from calypso_anemometer.model import CalypsoReading
from calypso_anemometer.exception import*
from calypso_anemometer.util import wait_forever

from .mqtt_modules import MqttPubModule
from modules.data_models.mqtt_packets import MQTTwindPkt
from .mqtt_utils import MqttTopics

class Calypso_Mini(MqttPubModule):
    def __init__(self, name: str, mqtt_broker: str = "localhost", mqtt_broker_port=1883) -> None:
        super().__init__([MqttTopics.WIND], mqtt_broker, mqtt_broker_port)
        log.debug(f"init calypso mini: {name}, {mqtt_broker}:{mqtt_broker_port}")
        self._name = name

        self._dev_settings = Settings(ble_discovery_timeout=5, ble_connect_timeout=20)
        self._device: CalypsoDeviceApi = CalypsoDeviceApi(self._dev_settings)

        # Setup gracefull exit on kill        
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    async def run(self):
        await self._device.discover()
        await self._device.connect()

        await self._device.subscribe_reading(self.process_reading)
        log.info("subscribe waiting forever")
        await wait_forever()
    
    def process_reading(self, reading:CalypsoReading):
        dt = datetime.datetime.utcnow()
        wind_Pkt = MQTTwindPkt(
                timestamp = int(dt.timestamp()), #int
                sender_name = self._name,
                wind_spd = reading.wind_speed,  #float
                wind_dir = reading.wind_direction #int
            )
        self.publish(MqttTopics.WIND, str(wind_Pkt))

    async def exit_gracefully(self, _1=None, _2=None):
        await self._device.disconnect()

class Anemometer(Calypso_Mini): pass

if __name__ == "__name__":
    log.basicConfig(level=log.DEBUG)
    ane = Anemometer("Calyso_Mini")
    log.info("Anemometer started, running.")
    asyncio.run(ane.run())
    input("Anemometer running, press any key to quit... \n")

