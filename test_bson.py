import bson
from mongita import MongitaClientDisk

client = MongitaClientDisk()
db = client['mydatabase']
coll = db['mycollection']

def insert_data(data):
    try:
        # Validate BSON data
        if not bson.is_valid(data):
            raise ValueError("Invalid BSON data")
        
        # Insert data into the collection
        coll.insert_one(data)
    except bson.errors.InvalidBSON as e:
        print(f"Invalid BSON data: {data}, error: {str(e)}")
    except ValueError as ve:
        print(f"Value error: {str(ve)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example data
data = {
    'time': 1688125705,
    'type': 'imu',
    'name': 'HUB IMU',
    'acc_x': -4.0625,
    'acc_y': 3.1796875,
    'acc_z': -8.2734375,
    'lin_x': 0.015625,
    'lin_y': -0.046875,
    'lin_z': -0.015625,
    'rot_w': 0.0716552734375,
    'rot_x': 0.9583740234375,
    'rot_y': 0.15362548828125,
    'rot_z': 0.229736328125,
    'gyr_x': 0.0,
    'gyr_y': 0.0,
    'gyr_z': 0.0
}

insert_data(data)