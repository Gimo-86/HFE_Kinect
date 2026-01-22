"""
配置檔案 - 集中管理所有設定參數
"""

import os

# === 數據源選擇 ===
# 相機模式："WEBCAM" (普通攝像頭), "KINECT" (Kinect + Body Tracking), "KINECT_RGB" (Kinect RGB + MediaPipe)
CAMERA_MODE = "KINECT"  # 可選: "WEBCAM", "KINECT", "KINECT_RGB"

# === 顯示模式選擇 ===
DISPLAY_MODE = "COORDINATES"  # "RULA": 顯示RULA評估分數; "COORDINATES": 顯示關鍵點坐標

# === Azure Kinect SDK 配置 ===
# 根據你的安裝路徑修改以下配置
KINECT_SDK_PATH = r"C:\Program Files\Azure Kinect SDK v1.4.1\sdk\windows-desktop\amd64\release\bin"
KINECT_BODY_TRACKING_PATH = r"C:\Program Files\Azure Kinect Body Tracking SDK\tools"

# Kinect 設備配置
KINECT_RESOLUTION = "1080P"  # 可選: 720P, 1080P, 1440P, 1536P, 2160P, 3072P
KINECT_DEPTH_MODE = "WFOV_2x2BINNED"  # 可選: NFOV_2x2BINNED, NFOV_UNBINNED, WFOV_2x2BINNED, WFOV_UNBINNED

def load_kinect_libraries():
    """載入 Azure Kinect SDK 和 Body Tracking SDK DLLs"""
    if os.path.exists(KINECT_SDK_PATH):
        os.add_dll_directory(KINECT_SDK_PATH)
    else:
        print(f"警告: Kinect SDK 路徑不存在: {KINECT_SDK_PATH}")
    
    if os.path.exists(KINECT_BODY_TRACKING_PATH):
        os.add_dll_directory(KINECT_BODY_TRACKING_PATH)
    else:
        print(f"警告: Kinect Body Tracking SDK 路徑不存在: {KINECT_BODY_TRACKING_PATH}")

# RULA 固定參數設定
RULA_CONFIG = {
    'wrist_twist': 1,        # 手腕扭轉參數
    'legs': 1,               # 腿部姿勢參數
    'muscle_use_a': 0,         # Table A 肌肉使用參數
    'muscle_use_b': 0,         # Table B 肌肉使用參數
    'force_load_a': 0,       # Table A 負荷力量參數
    'force_load_b': 0,       # Table B 負荷力量參數
}

# 角度計算參數
TOLERANCE_ANGLE = 5.0        # 容忍角度（度）
MIN_CONFIDENCE = 0.5         # 最小置信度閾值
USE_PREVIOUS_FRAME_ON_LOW_CONFIDENCE = False  # 低置信度處理策略

# MediaPipe 設定（即時辨識優化）
MEDIAPIPE_CONFIG = {
    'static_image_mode': False,
    'model_complexity': 0,      # 改為 0（最輕量模型，提升速度）
    'smooth_landmarks': True,
    'enable_segmentation': False,
    'smooth_segmentation': False,  # 關閉分割功能
    'min_detection_confidence': 0.5,
    'min_tracking_confidence': 0.5
}

# === Azure Kinect 關節映射 (新增) ===
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
