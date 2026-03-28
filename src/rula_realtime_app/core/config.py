"""
配置檔案 - 集中管理所有設定參數
"""

import os

# === 數據源選擇 ===
# 相機模式："WEBCAM" (普通攝像頭), "KINECT" (Kinect + Body Tracking), "KINECT_RGB" (Kinect RGB + MediaPipe)
CAMERA_MODE = "KINECT"  # 可選: "WEBCAM", "KINECT", "KINECT_RGB"

# === 顯示模式選擇 ===
DISPLAY_MODE = "COORDINATES"  # "RULA": 顯示RULA評估分數; "COORDINATES": 顯示關鍵點坐標

# === 介面語言設定 ===
APP_LANGUAGE = "zh-TW"  # 可選: "zh-TW", "en"

SUPPORTED_LANGUAGES = {
    "zh-TW": "繁體中文",
    "en": "English",
}

UI_TEXTS = {
    "zh-TW": {
        "window_title": "RULA 即時評估系統",
        "source_webcam": "攝像頭",
        "source_kinect": "Azure Kinect",
        "source_kinect_rgb": "Kinect RGB + MediaPipe",
        "waiting": "等待開始...",
        "stopped": "已停止",
        "start": "開始",
        "stop": "停止",
        "pause": "暫停",
        "resume": "繼續",
        "save": "💾 保存",
        "save_tooltip": "保存當前畫面和分數",
        "config_tooltip": "RULA 參數設定",
        "fps": "FPS",
        "left_panel_title": "左側 RULA 評估",
        "right_panel_title": "右側 RULA 評估",
        "coordinates_panel_title": "關鍵點坐標",
        "dialog_title": "RULA 預設參數設定",
        "dialog_heading": "調整 RULA 固定參數：",
        "language_label": "介面語言:",
        "param_wrist_twist": "手腕扭轉:",
        "param_legs": "腿部姿勢:",
        "param_muscle_use_a": "肌肉使用-手臂:",
        "param_muscle_use_b": "肌肉使用-身體:",
        "param_force_load_a": "負荷力量-手臂:",
        "param_force_load_b": "負荷力量-身體:",
        "param_desc_wrist_twist": "1=中立位置, 2=扭轉",
        "param_desc_legs": "1=平衡站立/坐姿, 2=不平衡",
        "param_desc_muscle_use": "0=無, 1=靜態/重複",
        "param_desc_force_load": "0=<2kg, 1=2-10kg, 2=>10kg",
        "option_0_none": "0 - 無",
        "option_1_static_repeat": "1 - 靜態/重複",
        "option_0_lt_2kg": "0 - <2kg",
        "option_1_2_to_10kg": "1 - 2-10kg",
        "option_2_gt_10kg": "2 - >10kg",
        "option_1_neutral": "1 - 中立位置",
        "option_2_twist": "2 - 扭轉",
        "option_1_balanced": "1 - 平衡站立/坐姿",
        "option_2_unbalanced": "2 - 不平衡",
        "save_button": "保存",
        "close_button": "關閉",
        "kinect_not_available": "Azure Kinect 不可用，請檢查 SDK 安裝",
        "kinect_rgb_not_available": "Kinect RGB 不可用，請檢查 SDK 安裝",
        "error_prefix": "錯誤",
        "error_title": "錯誤",
        "camera_connect_failed": "Azure Kinect 連接失敗",
        "generic_error": "發生錯誤",
        "warning_title": "警告",
        "no_frame_to_save": "沒有可保存的畫面",
        "save_success_title": "保存成功",
        "save_success_text": "文件已成功保存！",
        "save_failed": "保存失敗",
    },
    "en": {
        "window_title": "RULA Real-time Assessment",
        "source_webcam": "Webcam",
        "source_kinect": "Azure Kinect",
        "source_kinect_rgb": "Kinect RGB + MediaPipe",
        "waiting": "Waiting to start...",
        "stopped": "Stopped",
        "start": "Start",
        "stop": "Stop",
        "pause": "Pause",
        "resume": "Resume",
        "save": "💾 Save",
        "save_tooltip": "Save current frame and scores",
        "config_tooltip": "RULA parameter settings",
        "fps": "FPS",
        "left_panel_title": "Left RULA Assessment",
        "right_panel_title": "Right RULA Assessment",
        "coordinates_panel_title": "Keypoint Coordinates",
        "dialog_title": "RULA Default Parameter Settings",
        "dialog_heading": "Adjust fixed RULA parameters:",
        "language_label": "Language:",
        "param_wrist_twist": "Wrist Twist:",
        "param_legs": "Leg Posture:",
        "param_muscle_use_a": "Muscle Use - Arm:",
        "param_muscle_use_b": "Muscle Use - Body:",
        "param_force_load_a": "Force/Load - Arm:",
        "param_force_load_b": "Force/Load - Body:",
        "param_desc_wrist_twist": "1=neutral, 2=twisted",
        "param_desc_legs": "1=balanced standing/sitting, 2=unbalanced",
        "param_desc_muscle_use": "0=none, 1=static/repetitive",
        "param_desc_force_load": "0=<2kg, 1=2-10kg, 2=>10kg",
        "option_0_none": "0 - None",
        "option_1_static_repeat": "1 - Static/Repetitive",
        "option_0_lt_2kg": "0 - <2kg",
        "option_1_2_to_10kg": "1 - 2-10kg",
        "option_2_gt_10kg": "2 - >10kg",
        "option_1_neutral": "1 - Neutral",
        "option_2_twist": "2 - Twisted",
        "option_1_balanced": "1 - Balanced standing/sitting",
        "option_2_unbalanced": "2 - Unbalanced",
        "save_button": "Save",
        "close_button": "Close",
        "kinect_not_available": "Azure Kinect unavailable. Please check SDK installation.",
        "kinect_rgb_not_available": "Kinect RGB unavailable. Please check SDK installation.",
        "error_prefix": "Error",
        "error_title": "Error",
        "camera_connect_failed": "Azure Kinect connection failed",
        "generic_error": "An error occurred",
        "warning_title": "Warning",
        "no_frame_to_save": "No frame available to save",
        "save_success_title": "Save Successful",
        "save_success_text": "Files saved successfully!",
        "save_failed": "Save failed",
    },
}


def t(key, language=None):
    """Get localized UI text by key."""
    lang = language or APP_LANGUAGE
    language_pack = UI_TEXTS.get(lang, UI_TEXTS["zh-TW"])
    return language_pack.get(key, key)

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
    'legs': 2,               # 腿部姿勢參數
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
