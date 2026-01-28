"""
Azure Kinect 處理模組
使用 QThread 實現非阻塞的 Azure Kinect 影像讀取和骨架追蹤
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

from .config import (
    KINECT_TO_MEDIAPIPE, 
    K4ABT, 
    load_kinect_libraries,
    KINECT_RESOLUTION,
    KINECT_DEPTH_MODE
)


class KinectHandler(QThread):
    """
    Azure Kinect 處理執行緒
    負責讀取 Kinect 影像和骨架數據並透過信號發送
    """
    
    # 定義信號
    frame_ready = pyqtSignal(np.ndarray, list)  # 發送影像幀和 pose 數據 (pose array 格式)
    error_occurred = pyqtSignal(str)             # 發送錯誤訊息
    
    def __init__(self):
        """初始化 Kinect 處理器"""
        super().__init__()
        
        if not KINECT_AVAILABLE:
            raise RuntimeError("Azure Kinect SDK 未安裝")
        
        self.device = None
        self.body_tracker = None
        self.running = False
        
    def skeleton_to_pose_array(self, skeleton):
        """
        Convert Azure Kinect skeleton to MediaPipe-like pose array
        Returns: List of 33 landmarks, each [x, y, z, confidence]
        """
        pose = [[0.0, 0.0, 0.0, 0.0] for _ in range(33)]
        
        for mp_idx, kinect_idx in KINECT_TO_MEDIAPIPE.items():
            joint = skeleton.joints[kinect_idx]
            pos = joint.position.xyz
            # Normalize confidence from Azure Kinect (0-3) to 0-1 range
            conf_raw = getattr(joint, "confidence_level", 0)
            conf_norm = min(max(conf_raw / 3.0, 0.0), 1.0)
            
            # Convert mm to normalized coordinates (divide by 1000 for meters)
            pose[mp_idx] = [pos.x / 1000.0, pos.y / 1000.0, pos.z / 1000.0, conf_norm]
        
        return pose
        
    def run(self):
        """執行緒主循環"""
        try:
            # 1. 載入 Kinect SDK 庫
            load_kinect_libraries()
            
            # 2. 初始化庫 (track_body 必須為 True 以啟動骨架偵測功能)
            try:
                pykinect.initialize_libraries(track_body=True)
            except Exception as e:
                self.error_occurred.emit(f"Kinect SDK 初始化失敗: {str(e)}\n請確認 SDK 已正確安裝")
                return
            
            # 3. 修改相機配置
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
            
            # 根據配置設定深度模式
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
            
            # 5. 啟動 Body Tracker
            try:
                self.body_tracker = pykinect.start_body_tracker()
                if self.body_tracker is None:
                    raise Exception("Body Tracker 返回 None")
            except Exception as e:
                self.error_occurred.emit(f"Body Tracker 初始化失敗: {str(e)}\n請確認 Body Tracking SDK 已正確安裝")
                if self.device:
                    self.device.close()
                return
            
            self.running = True
            
            while self.running:
                # 獲取感測器捕捉數據
                capture = self.device.update()
                
                # 獲取骨架幀數據
                body_frame = self.body_tracker.update()
                
                # 獲取彩色影像
                ret, color_image = capture.get_color_image()
                
                if not ret:
                    continue
                
                # 只處理第一個偵測到的人體
                num_bodies = body_frame.get_num_bodies()
                pose = []  # 預設為空列表而非 None
                
                if num_bodies > 0:
                    skeleton = body_frame.get_body_skeleton(0)  # 獲取第一個人體
                    pose = self.skeleton_to_pose_array(skeleton)
                    # 繪製所有檢測到的骨架（pykinect_azure 沒有只繪製單個骨架的方法）
                    color_skeleton = body_frame.draw_bodies(color_image, pykinect.K4A_CALIBRATION_TYPE_COLOR)
                else:
                    # 沒有偵測到人體時，使用原始影像
                    color_skeleton = color_image
                
                # 轉換顏色空間 BGR -> RGB
                frame_rgb = cv2.cvtColor(color_skeleton, cv2.COLOR_BGR2RGB)
                
                # 發送影像和 pose 數據（pose 為列表，無人體時為空列表）
                self.frame_ready.emit(frame_rgb, pose)
                    
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
