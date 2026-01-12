"""
MediaPipe 骨架辨識模組
"""

import cv2
import numpy as np

# 延遲匯入 mediapipe，避免初始化問題
import mediapipe as mp

from .video_config import MEDIAPIPE_CONFIG


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
        取得關鍵點陣列（用於 RULA 計算）
        
        Returns:
            list: 33個關鍵點的 [x, y, z, visibility] 列表
                  若無偵測結果則返回 None
        """
        if self.results is None or self.results.pose_landmarks is None:
            return None
        
        landmarks = []
        for lm in self.results.pose_landmarks.landmark:
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
    
    def draw_angles(self, image, rula_data, side='Left'):
        """
        在影像上標註關鍵角度
        
        Args:
            image: RGB 格式的影像
            rula_data: RULA 計算結果字典
            side: 'Left' 或 'Right'
            
        Returns:
            numpy.ndarray: 標註後的影像
        """
        if self.results is None or self.results.pose_landmarks is None:
            return image
        
        annotated_image = image.copy()
        h, w = image.shape[:2]
        
        # 取得關鍵點位置
        landmarks = self.results.pose_landmarks.landmark
        
        # 根據側邊選擇關鍵點
        if side == 'Left':
            shoulder_idx = 11  # L_SHOULDER
            elbow_idx = 13     # L_ELBOW
            wrist_idx = 15     # L_WRIST
        else:
            shoulder_idx = 12  # R_SHOULDER
            elbow_idx = 14     # R_ELBOW
            wrist_idx = 16     # R_WRIST
        
        # 繪製角度文字
        def put_angle_text(landmark_idx, text, offset_x=10, offset_y=-10):
            if landmark_idx < len(landmarks):
                lm = landmarks[landmark_idx]
                x = int(lm.x * w) + offset_x
                y = int(lm.y * h) + offset_y
                cv2.putText(annotated_image, text, (x, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 標註各部位角度
        if 'upper_arm_angle' in rula_data and rula_data['upper_arm_angle'] != 'NULL':
            put_angle_text(shoulder_idx, f"Arm: {rula_data['upper_arm_angle']}", -60, 0)
        
        if 'lower_arm_angle' in rula_data and rula_data['lower_arm_angle'] != 'NULL':
            put_angle_text(elbow_idx, f"Elbow: {rula_data['lower_arm_angle']}", 10, -10)
        
        if 'wrist_angle' in rula_data and rula_data['wrist_angle'] != 'NULL':
            put_angle_text(wrist_idx, f"Wrist: {rula_data['wrist_angle']}", 10, 10)
        
        return annotated_image
    
    def close(self):
        """釋放資源"""
        if self.pose:
            self.pose.close()
