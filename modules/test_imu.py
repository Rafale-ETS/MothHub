import board
import busio
from adafruit_bno08x.i2c import BNO08X_I2C

i2c = busio.I2C(board.SCL, board.SDA)
sensor = BNO08X_I2C(i2c)

try:
    sensor.initialize()
    print("Sensor initialized successfully!")
except Exception as e:
    print(f"Error initializing sensor: {e}")