"""
核心功能模組
包含 RULA 計算、骨架辨識、攝像頭處理等核心功能
"""

from .rula_calculator import angle_calc, rula_score_side
from .utils import get_best_rula_score, safe_angle, check_confidence
from .config import (
    MEDIAPIPE_CONFIG, 
    RULA_CONFIG, 
    CAMERA_MODE, 
    KINECT_TO_MEDIAPIPE, 
    K4ABT,
    load_kinect_libraries,
    KINECT_SDK_PATH,
    KINECT_BODY_TRACKING_PATH,
    KINECT_RESOLUTION,
    KINECT_DEPTH_MODE
)

__all__ = [
    'angle_calc',
    'rula_score_side',
    'get_best_rula_score',
    'safe_angle',
    'check_confidence',
    'MEDIAPIPE_CONFIG',
    'RULA_CONFIG',
    'CAMERA_MODE',
    'KINECT_TO_MEDIAPIPE',
    'K4ABT',
    'load_kinect_libraries',
    'KINECT_SDK_PATH',
    'KINECT_BODY_TRACKING_PATH',
    'KINECT_RESOLUTION',
    'KINECT_DEPTH_MODE'
]
