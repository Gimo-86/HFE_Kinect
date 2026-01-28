"""
Azure Kinect RGB 相機處理模組（不使用 Body Tracking）
僅讀取 Kinect 的 RGB 影像，配合 MediaPipe 進行骨架檢測
"""

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import pykinect_azure as pykinect
    KINECT_AVAILABLE = True
except ImportError:
    KINECT_AVAILABLE = False
    print("警告: pykinect_azure 未安裝，無法使用 Azure Kinect")

from .config import load_kinect_libraries, KINECT_RESOLUTION, KINECT_DEPTH_MODE


class KinectRGBHandler(QThread):
    """
    Azure Kinect RGB 相機處理執行緒
    只讀取 RGB 影像，不進行骨架追蹤
    """
    
    # 定義信號
    frame_ready = pyqtSignal(np.ndarray)  # 發送 RGB 影像幀
    error_occurred = pyqtSignal(str)       # 發送錯誤訊息
    
    def __init__(self):
        """初始化 Kinect RGB 處理器"""
        super().__init__()
        
        if not KINECT_AVAILABLE:
            raise RuntimeError("Azure Kinect SDK 未安裝")
        
        self.device = None
        self.running = False
        
    def run(self):
        """執行緒主循環"""
        try:
            # 1. 載入 Kinect SDK 庫
            load_kinect_libraries()
            
            # 2. 初始化庫（不需要 body tracking）
            try:
                pykinect.initialize_libraries(track_body=False)
            except Exception as e:
                self.error_occurred.emit(f"Kinect SDK 初始化失敗: {str(e)}\n請確認 SDK 已正確安裝")
                return
            
            # 3. 配置相機
            device_config = pykinect.default_configuration
            
            # 根據配置設定分辨率
            if KINECT_RESOLUTION == "720P":
                device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
            elif KINECT_RESOLUTION == "1080P":
                device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
            elif KINECT_RESOLUTION == "1440P":
                device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1440P
            elif KINECT_RESOLUTION == "1536P":
                device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1536P
            elif KINECT_RESOLUTION == "2160P":
                device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_2160P
            elif KINECT_RESOLUTION == "3072P":
                device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_3072P
            else:
                device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
            
            # 深度模式（即使不使用深度，也需要設定）
            if KINECT_DEPTH_MODE == "NFOV_2x2BINNED":
                device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_2X2BINNED
            elif KINECT_DEPTH_MODE == "NFOV_UNBINNED":
                device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_UNBINNED
            elif KINECT_DEPTH_MODE == "WFOV_2x2BINNED":
                device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED
            elif KINECT_DEPTH_MODE == "WFOV_UNBINNED":
                device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_UNBINNED
            else:
                device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED
            
            # 4. 啟動設備
            try:
                self.device = pykinect.start_device(config=device_config)
            except BaseException as e:
                error_msg = f"Kinect 設備啟動失敗\n錯誤: {str(e)}\n\n請檢查:\n1. Kinect 是否正確連接 (USB 3.0 + 電源)\n2. 設備管理器中是否有 Azure Kinect 設備\n3. 是否有其他程式正在使用 Kinect"
                self.error_occurred.emit(error_msg)
                return
            
            # 檢查設備是否成功啟動
            if self.device is None or not hasattr(self.device, 'update'):
                error_msg = "無法連接 Azure Kinect 設備\n\n請檢查:\n1. Kinect 是否正確連接 (USB 3.0 + 電源)\n2. 設備管理器中是否有 Azure Kinect 設備\n3. 是否有其他程式正在使用 Kinect\n4. USB 連接埠是否為 USB 3.0"
                self.error_occurred.emit(error_msg)
                return
            
            self.running = True
            
            while self.running:
                # 獲取感測器捕捉數據
                capture = self.device.update()
                
                # 獲取彩色影像
                ret, color_image = capture.get_color_image()
                
                if not ret:
                    continue
                
                # 轉換顏色空間 BGR -> RGB
                frame_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
                
                # 發送影像
                self.frame_ready.emit(frame_rgb)
                    
        except Exception as e:
            self.error_occurred.emit(f"Kinect 錯誤: {str(e)}")
        finally:
            # 釋放資源
            if self.device is not None:
                self.device.close()
    
    def stop(self):
        """停止 Kinect"""
        self.running = False
        self.wait()  # 等待執行緒結束
