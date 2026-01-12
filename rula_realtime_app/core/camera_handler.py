"""
攝像頭處理模組
使用 QThread 實現非阻塞的攝像頭影像讀取
"""

import cv2
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np


class CameraHandler(QThread):
    """
    攝像頭處理執行緒
    負責讀取攝像頭影像並透過信號發送
    """
    
    # 定義信號
    frame_ready = pyqtSignal(np.ndarray)  # 發送影像幀
    error_occurred = pyqtSignal(str)       # 發送錯誤訊息
    fps_updated = pyqtSignal(float)        # 發送 FPS 數據
    
    def __init__(self, camera_index=0):
        """
        初始化攝像頭處理器
        
        Args:
            camera_index: 攝像頭索引，預設 0（前置鏡頭）
        """
        super().__init__()
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self.fps_counter = 0
        self.fps_timer = cv2.getTickCount()
        
    def run(self):
        """執行緒主循環"""
        # 開啟攝像頭
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            self.error_occurred.emit("無法開啟攝像頭")
            return
        
        # 設定攝像頭參數（降低解析度以提升效能）
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)   # 從 640 降到 480
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)  # 從 480 降到 360
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.running = True
        
        while self.running:
            ret, frame = self.cap.read()
            
            if not ret:
                self.error_occurred.emit("讀取影像失敗")
                break
            
            # 水平翻轉（鏡像模式）
            frame = cv2.flip(frame, 1)
            
            # 轉換顏色空間 BGR -> RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 發送影像
            self.frame_ready.emit(frame_rgb)
            
            # 計算 FPS
            self.fps_counter += 1
            if self.fps_counter >= 30:
                current_time = cv2.getTickCount()
                elapsed = (current_time - self.fps_timer) / cv2.getTickFrequency()
                fps = self.fps_counter / elapsed
                self.fps_updated.emit(fps)
                
                self.fps_counter = 0
                self.fps_timer = current_time
        
        # 釋放資源
        if self.cap is not None:
            self.cap.release()
    
    def stop(self):
        """停止攝像頭"""
        self.running = False
        self.wait()  # 等待執行緒結束
