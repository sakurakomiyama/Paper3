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
            



# calculate sunrise using NOAA equations
def sunrise(lat, lon, target_date, tz: str = "UTC") -> pd.Series:
    """
    Vectorized two-pass NOAA sunrise calculation for Pandas Series/DataFrame columns.
    Returns a Series of timezone-naive local timestamps (NaT during polar day/night).
    """
    lat_arr = np.asarray(lat, dtype=float)
    lon_arr = np.asarray(lon, dtype=float)
    dt_series = pd.to_datetime(target_date)

    # Normalize to midnight UTC for Julian Day calculation
    base_utc = dt_series.dt.floor("D").dt.tz_localize("UTC")

    year = dt_series.dt.year.to_numpy()
    month = dt_series.dt.month.to_numpy()
    day = dt_series.dt.day.to_numpy()

    def _sunrise_minutes(jd: np.ndarray) -> np.ndarray:
        t = (jd - 2451545.0) / 36525.0
        L0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
        M = 357.52911 + t * (35999.05029 - 0.0001537 * t)
        M_rad = np.radians(M)
        e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
        C = (
            np.sin(M_rad) * (1.914602 - t * (0.004817 + 0.000014 * t))
            + np.sin(2 * M_rad) * (0.019993 - 0.000101 * t)
            + np.sin(3 * M_rad) * 0.000289
        )
        sun_true_long = L0 + C
        omega = 125.04 - 1934.136 * t
        sun_app_long = sun_true_long - 0.00569 - 0.00478 * np.sin(np.radians(omega))

        mean_obliq = 23 + (26 + ((21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60)) / 60
        obliq_corr = mean_obliq + 0.00256 * np.cos(np.radians(omega))
        decl_rad = np.arcsin(
            np.sin(np.radians(obliq_corr)) * np.sin(np.radians(sun_app_long))
        )

        y_var = np.tan(np.radians(obliq_corr / 2)) ** 2
        L0_rad = np.radians(L0)
        eq_of_time = 4 * np.degrees(
            y_var * np.sin(2 * L0_rad)
            - 2 * e * np.sin(M_rad)
            + 4 * e * y_var * np.sin(M_rad) * np.cos(2 * L0_rad)
            - 0.5 * (y_var ** 2) * np.sin(4 * L0_rad)
            - 1.25 * (e ** 2) * np.sin(2 * M_rad)
        )

        lat_rad = np.radians(lat_arr)
        cos_ha = (np.cos(np.radians(90.833)) / (np.cos(lat_rad) * np.cos(decl_rad))) - (
            np.tan(lat_rad) * np.tan(decl_rad)
        )

        # Mask polar day/night values as NaN instead of raising domain errors
        valid = (cos_ha >= -1.0) & (cos_ha <= 1.0)
        ha_deg = np.full_like(cos_ha, np.nan, dtype=float)
        ha_deg[valid] = np.degrees(np.arccos(cos_ha[valid]))

        solar_noon_min = 720 - 4 * lon_arr - eq_of_time
        return solar_noon_min - ha_deg * 4

    # Julian Day at 00:00 UTC
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd_0 = jdn - 0.5

    # Two-pass calculation
    sunrise_min = _sunrise_minutes(jd_0)
    sunrise_min = _sunrise_minutes(jd_0 + sunrise_min / 1440.0)

    # Add offset in minutes, convert to target timezone, and return naive timestamps
    utc_sunrise = base_utc + pd.to_timedelta(sunrise_min, unit="m")
    return utc_sunrise.dt.tz_convert(tz).dt.tz_localize(None)




# calculate sunsetusing NOAA equations
def sunset(lat, lon, target_date, tz: str = "UTC") -> pd.Series:
    """
    Vectorized two-pass NOAA sunset calculation for Pandas Series/DataFrame columns.
    Returns a Series of timezone-naive local timestamps (NaT during polar day/night).
    """
    lat_arr = np.asarray(lat, dtype=float)
    lon_arr = np.asarray(lon, dtype=float)
    dt_series = pd.to_datetime(target_date)

    # Handle both timezone-naive and timezone-aware input Series safely
    if dt_series.dt.tz is not None:
        dt_series = dt_series.dt.tz_convert(tz).dt.tz_localize(None)

    base_utc = dt_series.dt.floor("D").dt.tz_localize("UTC")

    year = dt_series.dt.year.to_numpy()
    month = dt_series.dt.month.to_numpy()
    day = dt_series.dt.day.to_numpy()

    def _sunset_minutes(jd: np.ndarray) -> np.ndarray:
        t = (jd - 2451545.0) / 36525.0
        L0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
        M = 357.52911 + t * (35999.05029 - 0.0001537 * t)
        M_rad = np.radians(M)
        e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
        C = (
            np.sin(M_rad) * (1.914602 - t * (0.004817 + 0.000014 * t))
            + np.sin(2 * M_rad) * (0.019993 - 0.000101 * t)
            + np.sin(3 * M_rad) * 0.000289
        )
        sun_true_long = L0 + C
        omega = 125.04 - 1934.136 * t
        sun_app_long = sun_true_long - 0.00569 - 0.00478 * np.sin(np.radians(omega))

        mean_obliq = 23 + (26 + ((21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60)) / 60
        obliq_corr = mean_obliq + 0.00256 * np.cos(np.radians(omega))
        decl_rad = np.arcsin(
            np.sin(np.radians(obliq_corr)) * np.sin(np.radians(sun_app_long))
        )

        y_var = np.tan(np.radians(obliq_corr / 2)) ** 2
        L0_rad = np.radians(L0)
        eq_of_time = 4 * np.degrees(
            y_var * np.sin(2 * L0_rad)
            - 2 * e * np.sin(M_rad)
            + 4 * e * y_var * np.sin(M_rad) * np.cos(2 * L0_rad)
            - 0.5 * (y_var ** 2) * np.sin(4 * L0_rad)
            - 1.25 * (e ** 2) * np.sin(2 * M_rad)
        )

        lat_rad = np.radians(lat_arr)
        cos_ha = (np.cos(np.radians(90.833)) / (np.cos(lat_rad) * np.cos(decl_rad))) - (
            np.tan(lat_rad) * np.tan(decl_rad)
        )

        valid = (cos_ha >= -1.0) & (cos_ha <= 1.0)
        ha_deg = np.full_like(cos_ha, np.nan, dtype=float)
        ha_deg[valid] = np.degrees(np.arccos(cos_ha[valid]))

        solar_noon_min = 720 - 4 * lon_arr - eq_of_time
        return solar_noon_min + ha_deg * 4

    # Julian Day at 00:00 UTC
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd_0 = jdn - 0.5

    # Two-pass calculation
    sunset_min = _sunset_minutes(jd_0)
    sunset_min = _sunset_minutes(jd_0 + sunset_min / 1440.0)

    utc_sunset = base_utc + pd.to_timedelta(sunset_min, unit="m")
    return utc_sunset.dt.tz_convert(tz).dt.tz_localize(None)


