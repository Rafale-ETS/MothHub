import json
import logging as log
from threading import Lock
import time
#Gestion de la communication LoRa du Pi actuellement non operationnel
import serial
import paho.mqtt.client as mqtt

from modules.mqtt_utils import MqttTopics
from .mqtt_modules import MqttSubModule

class RF_REGION_MHZ:
    NORTH_AMERICA = 903.3
    EUROPE = 869.3

class AT_COMMANDS:
    AT = ""
    ID = "ID"
    MODE = "MODE"
    PTP = "TEST"

class MODES:
    TRANSMIT = "tx"
    RECIEVE = "rx"

class Serial_AT_Module:
    def __init__(self, serial_port: str, baud: int, region_MHz: float, start_mode: str) -> None:
        self.command_in_use = Lock()

        self.serial_connection = serial.Serial(serial_port, baud, timeout=30)

        self._sendCommand(AT_COMMANDS.MODE, AT_COMMANDS.PTP)
        self._sendCommand(AT_COMMANDS.PTP, "RFCFG," + str(region_MHz) + ",SF7,125,12,15,14,ON,OFF,OFF")
        
        self.isReciever = (start_mode is MODES.RECIEVE)
        if self.isReciever:
            # TODO: handle being a reciever
            #self.callback = recieveCallback
            #self._sendCommand(AT_COMMANDS.PTP, "RXLRPKT")
            #self._loopRecieve()
            pass

    def _sendCommand(self, command, parameterString):
        self.command_in_use.acquire()
        
        msg = "AT"
        if(command):
            msg += "+" + command
            
            if(parameterString):
                msg += "=" + parameterString
        
        msg += "\n\r"

        bmsg = bytes(msg, 'utf-8')
        self.serial_connection.write(bmsg)

        # TODO: a proper way to check that transaction is done
        line = self.serial_connection.readline()
        #line = self.serial_connection.readline()

        self.command_in_use.release()

    def sendString(self, string) -> bool:
        if(not self.isReciever):
            log.debug(f"AT_SEND: {string}")
            self._sendCommand(AT_COMMANDS.PTP, "TXLRSTR,\""+string+"\"")
            return True
        else:
            log.debug(f"AT_SEND: trying to send in recieve mode.")
            return False

        

class LoRa_E5(MqttSubModule):
    def __init__(self, region_MHz: float, serial_port: str, baud: int = 9600, mqtt_broker: str = "localhost", mqtt_broker_port: int = 1883) -> None:
        super().__init__(MqttTopics.ALL, mqtt_broker, mqtt_broker_port)

        self.at_modem = Serial_AT_Module(serial_port, baud, region_MHz, MODES.TRANSMIT)

        # Exceptionaly overwriting the on_message method of the mqtt client because we want it called on ANY topic.
        self.mqtt_clients[MqttTopics.ALL].client.on_message = self.on_message

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        log.debug(f"Recieved: [{msg.topic}]:{msg.payload.decode()}\n")
        string_msg = "{\"" + str(msg.topic) + "\": " + msg.payload.decode() + "}"
        self.at_modem.sendString(string_msg.replace('"', "'"))

#log.basicConfig(level=log.DEBUG)
log.debug("Starting...")
lora = LoRa_E5(RF_REGION_MHZ.NORTH_AMERICA, "COM4")

log.debug("Starting sleep loop")
while(1):
    time.sleep(0.5)
