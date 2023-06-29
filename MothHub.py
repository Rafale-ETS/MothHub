from threading import Thread
import logging as log
from paho.mqtt import client as mqtt_client
from time import sleep
import argparse
import asyncio

#from modules.gps import GPS
from modules.imu import IMU
from modules.local_archiving import Database as Local_DB
from modules.mqtt_utils import DEFAULT_BROKER, DEFAULT_PORT
from modules.anemometer2 import Anemometer

def isMQTTBrokerUp(broker: str = DEFAULT_BROKER, port: int = DEFAULT_PORT):
    broker_up = False

    def on_connect(client: mqtt_client.Client, userdata, result):
        log.info(f"{userdata}, {result}")
        nonlocal broker_up #use the parent's variable
        broker_up = True
    try:
        cl = mqtt_client.Client(client_id=None, clean_session=True, reconnect_on_failure=False)
        cl.on_connect = on_connect
        cl.connect(broker, port)

        sleep(2)

        cl.disconnect()
    except Exception as e:
        log.warning(f"Broker not found at {broker}:{port}, cause by exception:")
        log.warning(f"{e}")
        exit(1)

    return broker_up

def main():

    argParser = argparse.ArgumentParser()
    argParser.add_argument('-b', '--broker', type=str, help="The MQTT broker's IP address (string)", default=DEFAULT_BROKER, required=False)
    argParser.add_argument('-p', '--port', type=int, help="The MQTT broker's port. (int)", default=DEFAULT_PORT, required=False)
    argParser.add_argument('-v', '--verbose', help="Print debug outputs", required=False, action='store_true')
    argParser.add_argument('-s', '--silent', help="Print only warn and errors", required=False, action='store_true')

    args = argParser.parse_args()
    
    if args.verbose:
        log.basicConfig(level=log.DEBUG)
    elif args.silent:
        log.basicConfig(level=log.WARNING)
    else:
        log.basicConfig(level=log.INFO)

    log.info("Checking for MQTT Broker...")
    # TODO: fix
    #if not isMQTTBrokerUp(args.broker, args.port):
    #    log.warning(f"No MQTT broker found at {args.broker}:{args.port}, exiting.")
    #    exit(1)

    log.info("Broker found, Starting HUB...")    
#    gps = GPS("HUB GPS")
    imu = IMU("HUB IMU")
 #   anemo = Anemometer("Calypso Mini")
    local_DB = Local_DB("rafale3_local_archive") #Autostarts

 #   gps_thread = Thread(target=gps.run)
    imu_thread = Thread(target=imu.run)

  #  anemo_thread = Thread(target=asyncio.run, args=(anemo.run(),))

 #   gps_thread.start()
    imu_thread.start()
#    anemo_thread.start()

    log.info("Threads started. Waiting end...")

 #   gps_thread.join()
    imu_thread.join()
   # anemo_thread.join()

    log.warning("Threads ended, exiting!")

#    local_DB.exit_gracefully()
#    anemo.exit_gracefully()

    exit(0)

if __name__ == "__main__":
    main()
