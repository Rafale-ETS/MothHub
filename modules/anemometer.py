#anemometer python code
import asyncio
import datetime
import logging as log
#import signal

from modules.data_models.mqtt_packets import MQTTwindPkt
from .mqtt_utils import MqttTopics
from .mqtt_modules import MqttPubModule
from calypso_anemometer.core import CalypsoDeviceApi, Settings
from calypso_anemometer.model import CalypsoReading
from calypso_anemometer.util import wait_forever
from calypso_anemometer.exception import*

from aioretry import  retry, RetryPolicyStrategy, RetryInfo

def retry_policy(info: RetryInfo) -> RetryPolicyStrategy:
    return False, (info.fails - 1) % 3 * 0.1

@retry(retry_policy)
async def calypso_subscribe_demo():
    def process_reading(reading:CalypsoReading):
       
        #reading.dump()
        
        dt = datetime.datetime.utcnow()
        wind_Pkt= MQTTwindPkt(
                timestamp = int(dt.timestamp()), #int
                sender_name = "WIND",
                wind_spd = reading.wind_speed,  #float
                wind_dir = reading.wind_direction #int
            )
        client.publish(MqttTopics.WIND, str(wind_Pkt))

    async with CalypsoDeviceApi(settings=Settings(ble_discovery_timeout=5, ble_connect_timeout=20)) as calypso:

#        def exit_gracefully(_1, _2):
#            calypso.disconnect()

        # Setup gracefull exit on kill        
#        signal.signal(signal.SIGINT, exit_gracefully)
#        signal.signal(signal.SIGTERM, exit_gracefully)

        log.info("connected creating mqtt client")
        client = MqttPubModule([MqttTopics.WIND])
        
        await calypso.subscribe_reading(process_reading)
        log.info("subscribe waiting forever")
        await wait_forever()
        #await calypso.discover()
        #await calypso.connect()
        await calypso.about()

if __name__ == "__main__":  # pragma: nocover
    log.basicConfig(level=log.DEBUG)
    asyncio.run(calypso_subscribe_demo())
