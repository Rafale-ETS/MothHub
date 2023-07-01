import datetime
import time
import board
import busio
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import \
    BNO_REPORT_ACCELEROMETER, \
    BNO_REPORT_GYROSCOPE, \
    BNO_REPORT_LINEAR_ACCELERATION, \
    BNO_REPORT_ROTATION_VECTOR

import logging as log
from modules.data_models.mqtt_packets import MQTTOrientationPkt

from modules.mqtt_utils import MqttTopics
from .mqtt_modules import MqttPubModule

BNO085_I2C_ADDR = 0x4b

class BNO085IMU(MqttPubModule):
    def __init__(self, name: str, mqtt_broker: str = "localhost", mqtt_broker_port=1883) -> None:
        super().__init__([MqttTopics.ORIENTATION], mqtt_broker, mqtt_broker_port)
        self._name = name

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.bno = BNO08X_I2C(self.i2c, address=BNO085_I2C_ADDR)

        self.bno.enable_feature(BNO_REPORT_ACCELEROMETER)
        self.bno.enable_feature(BNO_REPORT_GYROSCOPE)
        self.bno.enable_feature(BNO_REPORT_LINEAR_ACCELERATION)
        self.bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)

        #TODO: Calibrate?
    def run(self):
        while 1:
            timestamp = int(datetime.datetime.utcnow().timestamp())
            orientation = MQTTOrientationPkt(timestamp, self._name, self.bno.acceleration, 
                                            self.bno.linear_acceleration, self.bno.quaternion, self.bno.gyro)

            log.debug(str(orientation))
            self.publish(MqttTopics.ORIENTATION, str(orientation))

            # Run more or less 10 times per seconds
            time.sleep(1)

class IMU(BNO085IMU): pass

if __name__ == "__name__":
    imu = IMU("HUB IMU")
    imu.run()

    input("Imu running, press any key to quit... \n")
