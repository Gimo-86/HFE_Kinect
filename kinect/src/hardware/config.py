import json
import os
from pathlib import Path

# Load settings from JSON file
config_path = Path(__file__).parent / "settings.json"
with open(config_path, "r") as file:
    settings = json.load(file)

# Use the values from JSON
SDK_BIN = settings["sdk_path"]
BT_BIN = settings["body_tracking_path"]

def load_libraries():
    """Load Azure Kinect SDK and Body Tracking SDK DLLs."""
    if os.path.exists(SDK_BIN):
        os.add_dll_directory(SDK_BIN)
    if os.path.exists(BT_BIN):
        os.add_dll_directory(BT_BIN)


# Azure Kinect joint indices (K4ABT)
K4ABT = {
    "PELVIS": 0,
    "SPINE_NAVAL": 1,
    "SPINE_CHEST": 2,
    "NECK": 3,
    "CLAVICLE_LEFT": 4,
    "SHOULDER_LEFT": 5,
    "ELBOW_LEFT": 6,
    "WRIST_LEFT": 7,
    "HAND_LEFT": 8,
    "HANDTIP_LEFT": 9,
    "THUMB_LEFT": 10,
    "CLAVICLE_RIGHT": 11,
    "SHOULDER_RIGHT": 12,
    "ELBOW_RIGHT": 13,
    "WRIST_RIGHT": 14,
    "HAND_RIGHT": 15,
    "HANDTIP_RIGHT": 16,
    "THUMB_RIGHT": 17,
    "HIP_LEFT": 18,
    "KNEE_LEFT": 19,
    "ANKLE_LEFT": 20,
    "FOOT_LEFT": 21,
    "HIP_RIGHT": 22,
    "KNEE_RIGHT": 23,
    "ANKLE_RIGHT": 24,
    "FOOT_RIGHT": 25,
    "HEAD": 26,
    "NOSE": 27,
    "EYE_LEFT": 28,
    "EAR_LEFT": 29,
    "EYE_RIGHT": 30,
    "EAR_RIGHT": 31,
}

# Map Azure Kinect joints into a MediaPipe-like pose array (33 entries, each [x, y, z, conf]).
# Only the indices used by rula_calculator need to be populated; others stay zeros.
KINECT_TO_MEDIAPIPE = {
    0: K4ABT["NOSE"],          # NOSE
    7: K4ABT["EAR_LEFT"],      # LEFT EAR
    8: K4ABT["EAR_RIGHT"],     # RIGHT EAR
    11: K4ABT["SHOULDER_LEFT"],
    12: K4ABT["SHOULDER_RIGHT"],
    13: K4ABT["ELBOW_LEFT"],
    14: K4ABT["ELBOW_RIGHT"],
    15: K4ABT["WRIST_LEFT"],
    16: K4ABT["WRIST_RIGHT"],
    # Use thumb as pinky proxy and handtip as index proxy to satisfy hand center calc.
    17: K4ABT["HAND_LEFT"],   # LEFT WRIST (equivlalent mid point calculations later)
    18: K4ABT["HAND_RIGHT"],  # RIGHT WRIST (equivalent mid point calc later)
    19: K4ABT["HAND_LEFT"],   # LEFT WRIST (equivalent mid point calc later)
    20: K4ABT["HAND_RIGHT"],  # RIGHT WRIST (equivalent mid point calc later)
    23: K4ABT["HIP_LEFT"],
    24: K4ABT["HIP_RIGHT"],
}