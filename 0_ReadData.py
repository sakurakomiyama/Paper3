import pyreadr # to read .Rdata files
import os
import pandas as pd
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

#=================================#
####    Schools during event   ####
#=================================#

# [Step1] predator echograms: manually detected predator-like echograms, save as png
echograms = [f.name for f in os.scandir('C:\\Users\\xiz011\\OneDrive - University of Bergen\\Desktop\\Paper3\\Echogram') if f.is_file() and f.name.endswith(".png")] #f.name -> on.y file name / f.path -> entire path
file_name = echograms
echograms = [item.replace(".png", "") for item in echograms]
platform = [item.split('_')[0] for item in echograms]
date = [item.split('_')[1] for item in echograms]
time = [item.split('_')[2] for item in echograms]
note = [parts[3] if len(parts := item.split('_')) > 3 else 'NA' for item in echograms]
event_df = pd.DataFrame(list(zip(platform, date, time, note, file_name)), columns = ["platform", "date", "time", "note", "filename"])

event_df[["start_hm", "end_hm"]] = event_df["time"].str.extract(r"T(\d{4})-(\d{4})")
event_df["starttime"] = pd.to_datetime("2019" + event_df["date"] + event_df["start_hm"], format="%Y%m%d%H%M")
event_df["endtime"] = pd.to_datetime("2019" + event_df["date"] + event_df["end_hm"], format="%Y%m%d%H%M")
event_df = event_df.drop(columns=["start_hm", "end_hm"])

# [Step2] camera data: manually saving seabirds/dolphins/unclear images, around the predator echograms
camera_dir = Path(r"C:\Users\xiz011\OneDrive - University of Bergen\Desktop\Paper3\Camera")
rows = []

for file_path in camera_dir.rglob("*"):
    if not file_path.is_file() or file_path.suffix.lower() not in {".jpg", ".jpeg"}:
        continue    
    filename = file_path.stem # Remove the file extension
    parts = filename.split("_")

    # Get the first subfolder below Camera
    relative_parts = file_path.relative_to(camera_dir).parts

    if len(relative_parts) > 1:
        category = relative_parts[0]       # Dolphin, Seabird, etc.
    else:
        category = "Camera"                # Image directly in Camera

    row = {
        "platform": parts[0] if len(parts) > 0 else "NA",
        "date": parts[1] if len(parts) > 1 else "NA",
        "time": parts[2] if len(parts) > 2 else "NA",
        "note": parts[4] if len(parts) > 4 else "NA",
        "category": category,
        "filename": file_path.name
    }

    rows.append(row)

camera_df = pd.DataFrame(rows)
camera_df["datetime"] = pd.to_datetime("2019" + camera_df["date"] + camera_df["time"], format="%Y%m%d%H%M%S")


# [Step3] find match between echograms and camera data
tolerance = pd.Timedelta(minutes=30)
rows = []
matched_camera_indices = set()

for event_index, event in event_df.iterrows():

    # Camera times from 30 minutes before event start
    # until 30 minutes after event end
    matching_cameras = camera_df[
        (camera_df["platform"] == event["platform"]) &
        (camera_df["datetime"] >= event["starttime"] - tolerance) &
        (camera_df["datetime"] <= event["endtime"] + tolerance)
    ]

    if matching_cameras.empty:
        # Echogram without a matching camera
        rows.append({
            "platform": event["platform"],
            "datetime": event["starttime"],
            "Echogram": event["filename"],
            "Camera": None,
            "Camera_time": None,
            "Category": None
        })

    else:
        # One row for every matching camera
        for camera_index, camera in matching_cameras.iterrows():
            rows.append({
                "platform": camera["platform"],
                "datetime": event["starttime"],
                "Echogram": event["filename"],
                "Camera": camera["filename"],
                "Camera_time": camera["datetime"],
                "Category": camera["category"]
            })

            matched_camera_indices.add(camera_index)

# Add cameras without any matching echogram
for camera_index, camera in camera_df.iterrows():

    if camera_index not in matched_camera_indices:
        rows.append({
            "platform": camera["platform"],
            "datetime": camera["datetime"],
            "Echogram": None,
            "Camera": camera["filename"],
            "Camera_time": camera["datetime"],
            "Category": camera["category"]
        })

match_df = pd.DataFrame(
    rows,
    columns=["platform", "datetime", "Echogram", "Camera", "Category"]
)

match_df = match_df.sort_values(["platform", "datetime"]).reset_index(drop=True)

filtered_df = match_df.dropna( subset=["Echogram", "Camera"]).reset_index(drop=True)
filtered_df = filtered_df[filtered_df["Category"] != "Other"].copy()
filtered_df = filtered_df.sort_values(["platform", "datetime"]).reset_index(drop=True)


# [Step4] manually confirm each event
unique_events = (
    filtered_df[["platform", "datetime"]].drop_duplicates()
    .sort_values(["platform","datetime"]).reset_index(drop=True))
unique_events["event"] = ""   # empty column to fill in
unique_events.to_csv("events_to_label.csv", index=False)

#----------------------------------------------------------------#
# Manual check is done on 17.11.2026 by Sakura
# 1. show each event echogram
# 2. check if there are fish schools around (about 30mins before and after)
# 3. check r(f), >1 : sandeel, <1 : other
# 4. determine the certainty level of the echoes 0(not predator) ~ 3(certainly from predator)
# 5. predict predator type by camera only for certainty = 3 and some for seabirds
# 6. manually input the information to excel sheet "events_to_label.csv"
# 7. save as "events_labeled.csv"         
# last update 2026.11.17
#----------------------------------------------------------------#

# 
unique_event_df = pd.read_csv("events_labeled.csv", sep=";")

unique_event_df = unique_event_df[
    (unique_event_df["predator_certainty"] >=2) 
    & (unique_event_df["predator_type"].notna())
    & (unique_event_df["event"] == "predator-prey")
    & (unique_event_df["sandeel"].notna())].copy()


# [Step5] retrieve sandeel schools during the events

# first, extract predators echoes in LSSS
# *upper boundary 1m
# *deliniate predator school regions at 200kHz
# *(Conditions) sV threshold: -30 to -55dB 
#               color: green-red
#               Avoid echoes which connect to the surface (1m)
# *export sV files incl.38,200kHz 
# *export TS file at 38, 200kHz

# second, extract all fish schools 30mins before and after the predator echoes
# read data from .Rdata files that were already classified as Sandeel in Komiyama et al (2024).
school = pyreadr.read_r('C:\Data/School.RData')
first_key = list(school.keys())[0]
school_df = school[first_key]
school_df = school_df[(school_df["vessel"] != "EROS")
    & (school_df["category"] != "noise")].copy()

# read newly scrutinised sandeel schools
sand_added = pyreadr.read_r('sandeel.RData')
first_key = list(sand_added.keys())[0]
added_df = sand_added[first_key]

# concate to the school_df
school_df = pd.concat([school_df, added_df], ignore_index=True)


# read predator data
pred = pyreadr.read_r('predator.RData')
first_key = list(pred.keys())[0]
predator_df = pred[first_key]

# divide school "during-predation" and "non-predation"
predator_df["datetime"] = pd.to_datetime(predator_df["YMD_time"])
school_df["datetime"] = pd.to_datetime(school_df["YMD_time"])

school_df["predation"] = "non-predation"
for _, predator in predator_df.iterrows():
    vessel = predator["vessel"]
    start = predator["datetime"] - tolerance
    end = predator["datetime"] + tolerance

    mask = (
        (school_df["vessel"] == vessel) &
        (school_df["datetime"] >= start) &
        (school_df["datetime"] <= end)
    )

    school_df.loc[mask, "predation"] = "predation"


school200_df = school_df[school_df["Frequency"] == 200].copy()


# read sandeel schools result from LDA
sandeel = pyreadr.read_r("C:/Data/LDAresult_80TrainData_14var_excl.smallschools_alter.rf/sandeel.Rdata")
first_key = list(sandeel.keys())[0]
sandeel_df = sandeel[first_key]

school200_df["type"] = school200_df["id"].isin(sandeel_df["id"]).map({
    True: "sandeel",
    False: "other"
})

school200_df.groupby(["type"])["predation"].value_counts()


#==================================#
####     Analysis and plot      ####
#==================================#
#%matplotlib qt

#============================================================================================================================#
# histogram
plt.figure(); plt.hist(school200_df[(school200_df["type"] == "sandeel") & (school200_df["predation"] == "predation")]["meanDepth"]); plt.show()
plt.figure(); plt.hist(school200_df[(school200_df["type"] == "sandeel") & (school200_df["predation"] == "non-predation")]["meanDepth"]); plt.show()
#============================================================================================================================#




#============================================================================================================================#
# boxplot sV_mean, meanDepth,
plt.figure()
sns.boxplot(data=school200_df[school200_df["type"] == "sandeel"], 
            x="predation", y="sV_mean", log_scale = True, 
            order=["non-predation", "predation"]
           )
plt.show()



plt.figure()
sns.boxplot(data=school200_df[school200_df["type"] == "sandeel"], 
            x="predation", y="meanDepth", log_scale = False, 
            order=["non-predation", "predation"]
           )
plt.gca().invert_yaxis()
plt.show()
#============================================================================================================================#