"""
配置檔案 - 集中管理所有設定參數
"""

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
# === Sampling settings (新增) ===
ENABLE_VALID_FRAME_SAMPLING = False           # 是否啟用有效影格等間距採樣
VALID_FRAME_SAMPLING_EVERY = 3               # 等間距採樣步長：每幾張有效影格留一張
SAMPLED_FRAME_IMAGE_FORMAT = "jpg"           # 影像格式：'jpg' 或 'png'
SAMPLED_FRAME_DIR_NAME = "sampled_frames"    # 採樣影像存放的子資料夾名稱
SAMPLED_CSV_NAME = "valid_samples.csv"       # 對照表 CSV 檔名
SAMPLED_JPG_QUALITY = 95                     # JPG 品質(1-100)，僅 jpg 有效
