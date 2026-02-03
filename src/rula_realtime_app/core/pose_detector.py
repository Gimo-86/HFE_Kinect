"""
MediaPipe 骨架辨識模組
"""

import cv2
import numpy as np

# 延遲匯入 mediapipe，避免初始化問題
import mediapipe as mp

from .config import MEDIAPIPE_CONFIG


class PoseDetector:
    """
    MediaPipe Pose 骨架辨識器
    """
    
    def __init__(self):
        """初始化 MediaPipe Pose"""
        # 使用標準匯入方式
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        
        self.mp_pose = mp_pose
        self.mp_drawing = mp_drawing
        self.mp_drawing_styles = mp_drawing_styles
        
        # 創建 Pose 物件
        self.pose = mp_pose.Pose(
            static_image_mode=MEDIAPIPE_CONFIG['static_image_mode'],
            model_complexity=MEDIAPIPE_CONFIG['model_complexity'],
            smooth_landmarks=MEDIAPIPE_CONFIG['smooth_landmarks'],
            enable_segmentation=MEDIAPIPE_CONFIG['enable_segmentation'],
            smooth_segmentation=MEDIAPIPE_CONFIG['smooth_segmentation'],
            min_detection_confidence=MEDIAPIPE_CONFIG['min_detection_confidence'],
            min_tracking_confidence=MEDIAPIPE_CONFIG['min_tracking_confidence']
        )
        
        self.results = None
        
    def process_frame(self, frame):
        """
        處理單一影像幀
        
        Args:
            frame: RGB 格式的影像（numpy array）
            
        Returns:
            bool: 是否成功偵測到骨架
        """
        # MediaPipe 需要 RGB 格式
        self.results = self.pose.process(frame)
        
        return self.results.pose_landmarks is not None
    
    def get_landmarks_array(self):
        """
        取得關鍵點陣列（用於 RULA 計算）- 使用世界坐標
        
        Returns:
            list: 33個關鍵點的 [x, y, z, visibility] 列表（米為單位的世界坐標）
                  若無偵測結果則返回 None
        """
        if self.results is None or self.results.pose_world_landmarks is None:
            return None
        
        landmarks = []
        for lm in self.results.pose_world_landmarks.landmark:
            landmarks.append([lm.x, lm.y, lm.z, lm.visibility])
        
        return landmarks
    
    def draw_landmarks(self, image):
        """
        在影像上繪製骨架關鍵點
        
        Args:
            image: RGB 格式的影像（numpy array）
            
        Returns:
            numpy.ndarray: 繪製後的影像
        """
        if self.results is None or self.results.pose_landmarks is None:
            return image
        
        # 複製影像以避免修改原始影像
        annotated_image = image.copy()
        
        # 繪製骨架連線
        self.mp_drawing.draw_landmarks(
            annotated_image,
            self.results.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        return annotated_image
    
    def close(self):
        """釋放資源"""
        if self.pose:
            self.pose.close()
