import datetime
import serial 
import logging as log
from pynmeagps import NMEAReader, NMEAMessage

from modules.data_models.mqtt_packets import MQTTPositionPkt, MQTTSpeedPkt, PacketTypes, MQTTStatusPkt

from .mqtt_utils import MqttTopics
from .mqtt_modules import MqttPubModule

ZED_F9P_SERIAL_PORT = "/dev/ttyACM0"
ZED_F9P_SERIAL_BAUD = 38400
ZED_F9P_I2C_ADDR = 0x84

# Available message types: 
# ['$GNRMC', '$GNVTG', '$GNGGA', '$GNGSA', '$GPGSV', '$GLGSV', '$GAGSV', '$GBGSV', '$GNGLL']

# Used:
# RMC: Position, time
# VTG: Speed over ground
# GGA: Position, quality
NMEA_MESSAGE_GSA = "GSA"
NMEA_MESSAGE_RMC = "RMC"
NMEA_MESSAGE_VTG = "VTG"
NMEA_MESSAGE_GGA = "GGA"
NMEA_MESSAGE_GSV = "GSV"
NMEA_MESSAGE_GLL = "GLL"

class ZED_F9P_Hat_GPS(MqttPubModule):
    def __init__(self, name: str, mqtt_broker: str = "localhost", mqtt_broker_port=1883, serial_port=ZED_F9P_SERIAL_PORT, baud=ZED_F9P_SERIAL_BAUD) -> None:
        super().__init__([MqttTopics.POSITION, MqttTopics.SPEED], mqtt_broker, mqtt_broker_port)

        self._name = name
        self.serial_con = serial.Serial(serial_port, baud, timeout=5)
        self.nmea_stream = NMEAReader(self.serial_con)

    def run(self): # This is an infinite loop pooling the gps
        pos_data = MQTTPositionPkt(pkt_type=PacketTypes.gps_pos, sender_name=self._name)
        
        while True:
            try:
                parsed_msg: NMEAMessage = None
                _, parsed_msg = self.nmea_stream.read()
                # TODO: actuall logging 
                log.debug(f"{parsed_msg}")

                dt: datetime.datetime = datetime.datetime.utcnow()
                    
                if(parsed_msg.msgID == NMEA_MESSAGE_RMC):
                    pos_data = MQTTPositionPkt(pkt_type=PacketTypes.gps_pos, sender_name=self._name)
                    # RMC message is the first relevant message we get per data burst, we can use it to send the timestamp for the whole burst.
                    pos_data.time = int(dt.timestamp()) # time as a unix timestamp
                    pos_data.lon = parsed_msg.lon
                    pos_data.lonEW = parsed_msg.EW
                    pos_data.lat = parsed_msg.lat
                    pos_data.latNS = parsed_msg.NS
                    pos_data.add_data("nav_status", parsed_msg.navStatus)

                elif(parsed_msg.msgID == NMEA_MESSAGE_GGA):
                    pos_data.add_data("quality", parsed_msg.quality)
                    pos_data.add_data("sat_nbr", parsed_msg.numSV)
                    pos_data.add_data("h_precision", parsed_msg.HDOP) #in meters
                    pos_data.add_data("altitude", parsed_msg.alt)
                    pos_data.add_data("alt_unit", parsed_msg.altUnit)
                    pos_data.add_data("geoid_sep", parsed_msg.sep)
                    pos_data.add_data("geoid_sep_unit", parsed_msg.sepUnit)

                    # The GGA message is the last (relevant) message we get for each data burst
                    self.publish(MqttTopics.POSITION, str(pos_data))
                    pos_data.reset_to_default()
                    pos_data.type = PacketTypes.gps_pos
                    dt = datetime.datetime.utcnow()

                elif(parsed_msg.msgID == NMEA_MESSAGE_VTG):
                    spd_data = MQTTSpeedPkt(
                        timestamp = int(dt.timestamp()),
                        pkt_type = PacketTypes.gps_spd,
                        sender_name = self._name,
                        speed = parsed_msg.sogn, # Speed by default in knots
                        speed_unit = parsed_msg.sognUnit,
                        direction = parsed_msg.cogt, # Course over groub by default in degree true
                        direction_unit = parsed_msg.cogtUnit
                    )
                    spd_data.add_data_mul_dict({"speed_kmh": parsed_msg.sogk, "dir_mag": parsed_msg.cogm})

                    self.publish(MqttTopics.SPEED, str(spd_data))
            except Exception as e:
                log.error(e)
                status_data = MQTTStatusPkt(
                    timestamp = int(dt.timestamp()),
                    sender_name = self._name,
                    status = ["GPS Error"],
                    msg = f"{e}"
                )
                self.publish(MqttTopics.STATUS, str(status_data))

class GPS(ZED_F9P_Hat_GPS): pass

if __name__ == "__main__":
    log.basicConfig(level=log.DEBUG)
    gps = GPS(name="HUB GPS")
    gps.run()
