import numpy as np #version less than 2, but upgraded 2.2.6 (checked 20260717),
import pandas as pd # upgraded version 3.0.3 20260717 from v2.2.3
from geopy.distance import geodesic
from datetime import datetime # for "to_csv_wdatetime" function
import os
import math
import re
from pathlib import Path



#=======================#
#   General functions   #
#=======================#


#=========================================================================#
# save as csv
def to_csv_wdatetime(df, filename='data', sep='\t', date = True, message = True):
    if date == True:
        date_str = datetime.now().strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
        name = f"{filename}_{date_str}.txt"
        # Check for existing files, and append a number if needed
        counter = 1
        while os.path.exists(name):
            name = f"{filename}_{date_str} ({counter}).txt"
            counter += 1
    else:
        name = f"{filename}.txt"

    # Save the DataFrame to the CSV file
    df.to_csv(name, header=True, index=None, sep=sep, mode='w')
    if message:
        print(f"Data saved to {name}")


# calculate cartesian coordinate from lat lon
def gps_to_cartesian(lat, lon, alt):
    trans_gps_to_xyz = Transformer.from_crs(4979, 4978, always_xy=True)
    x, y, z = trans_gps_to_xyz.transform(lon, lat, alt)
    return x, y


# calculate angle between two gps positions
def calculate_angle(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    angle_radians = math.atan2((y2-y1), (x2-x1))
    angle_degrees = math.degrees(angle_radians)

    '''
    # 0 degree point positive x-axis (East)
    if angle_degrees < 0:
        angle_degrees += 360
    '''

    # Adjust to make 0 degrees point North
    angle_degrees = (90 - angle_degrees) % 360  # Move to navigation system where North is 0

    return angle_degrees


# change Saildrone jpeg file names
def change_camera_data_names(prefix, directory):
    for entry in folder_path.iterdir():
        if entry.is_file() and entry.suffix.lower() in (".jpg", ".jpeg"):
            oldname = entry.name
            




    