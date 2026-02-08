"""
主視窗 UI
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
import numpy as np
import cv2
import os
from datetime import datetime

from ..core.camera_handler import CameraHandler
from ..core.pose_detector import PoseDetector
from ..core import angle_calc, get_best_rula_score
from ..core import config as core_config

from .styles import *
from .components import ScorePanel, CoordinatesPanel, FrameRenderer, SnapshotManager
from .dialogs import RULAConfigDialog


# 嘗試導入所有可能的相機模組（動態判斷）
try:
    from ..core.kinect_handler import KinectHandler
    KINECT_AVAILABLE = True
except Exception as e:
    print(f"警告: 無法載入 Kinect 模組: {e}")
    KINECT_AVAILABLE = False

try:
    from ..core.kinect_rgb_handler import KinectRGBHandler
    KINECT_RGB_AVAILABLE = True
except Exception as e:
    print(f"警告: 無法載入 Kinect RGB 模組: {e}")
    KINECT_RGB_AVAILABLE = False


class MainWindow(QMainWindow):
    """
    RULA 即時評估主視窗
    """
    
    def __init__(self):
        super().__init__()
        
        # 從 config 動態讀取相機模式
        self.camera_mode = core_config.CAMERA_MODE
        
        # 根據配置設定視窗標題
        source_types = {
            "WEBCAM": "攝像頭",
            "KINECT": "Azure Kinect",
            "KINECT_RGB": "Kinect RGB + MediaPipe"
        }
        source_type = source_types.get(self.camera_mode, "攝像頭")
        self.setWindowTitle(f"RULA 即時評估系統 - {source_type}")
        self.setGeometry(100, 100, 1400, 700)  # 加寬視窗
        
        # 核心元件
        self.camera_handler = None
        self.kinect_handler = None
        self.kinect_rgb_handler = None
        # 只有非 Kinect Body Tracking 模式才需要 MediaPipe
        self.pose_detector = None if self.camera_mode == "KINECT" else PoseDetector()
        
        # RULA 計算用的前一幀資料
        self.prev_left = None
        self.prev_right = None
        
        # 當前影像
        self.current_frame = None
        
        # FPS 資訊
        self.current_fps = 0.0
        self.fps_counter = 0
        self.fps_timer = cv2.getTickCount()
        
        # 暫停狀態
        self.is_paused = False
        
        # 處理計數器（降低 RULA 計算頻率）
        self.frame_counter = 0
        self.rula_calc_every_n_frames = 5  # 每5幀才計算一次 RULA（降低計算負擔）
        
        # 最後的骨架繪製結果（用於未處理的幀）
        self.last_annotated_frame = None
        
        # 倒數保存功能
        self.countdown_active = False
        self.countdown_value = 0
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.frame_to_save = None
        
        # 顯示模式 - 從 config 模組動態讀取
        self.display_mode = core_config.DISPLAY_MODE  # "RULA" 或 "COORDINATES"
        
        # 錄影相關變數
        self.is_recording = False
        self.video_writer = None
        self.recording_start_time = None
        self.recording_frame_count = 0
        self.rula_records = []  # 記錄每一幀的 RULA 分數
        self.recording_filename = None
        self.recording_video_path = None  # 實際視頻文件路徑
        
        # 初始化 UI
        self.init_ui()
        
    def init_ui(self):
        """初始化使用者介面"""
        # 設定整體樣式
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # 主容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # === 左側：影像顯示區域 ===
        left_layout = QVBoxLayout()
        
        # 影像標籤
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setMaximumSize(960, 720)  # 增加最大尺寸以容納更大的畫面
        self.video_label.setStyleSheet(VIDEO_LABEL_STYLE)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("等待開始...")
        left_layout.addWidget(self.video_label)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("開始")
        self.start_button.clicked.connect(self.start_detection)
        self.start_button.setStyleSheet(START_BUTTON_STYLE)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_detection)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(STOP_BUTTON_STYLE)
        button_layout.addWidget(self.stop_button)
        
        self.pause_button = QPushButton("暫停")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setEnabled(False)
        self.pause_button.setStyleSheet(PAUSE_BUTTON_STYLE)
        button_layout.addWidget(self.pause_button)
        
        self.save_button = QPushButton("💾 保存")
        self.save_button.clicked.connect(self.save_snapshot)
        self.save_button.setEnabled(False)
        self.save_button.setToolTip("保存當前畫面和分數")
        self.save_button.setStyleSheet(SAVE_BUTTON_STYLE)
        button_layout.addWidget(self.save_button)
        
        self.record_button = QPushButton("⏺ 錄影")
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setEnabled(False)
        self.record_button.setToolTip("開始/停止錄影")
        self.record_button.setStyleSheet(RECORD_BUTTON_READY_STYLE)
        button_layout.addWidget(self.record_button)
        
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet(FPS_LABEL_STYLE)
        button_layout.addWidget(self.fps_label)
        
        # 參數設定按鈕（齒輪圖案）
        self.config_button = QPushButton("⚙")
        self.config_button.clicked.connect(self.show_config_dialog)
        self.config_button.setToolTip("RULA 參數設定")
        self.config_button.setStyleSheet(CONFIG_BUTTON_STYLE)
        button_layout.addWidget(self.config_button)
        
        button_layout.addStretch()
        left_layout.addLayout(button_layout)
        
        main_layout.addLayout(left_layout, stretch=3)  # 左側佔3份
        
        # === 右側：評估面板 ===
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        # 設定右側面板容器的最小寬度（移除最大寬度限制，讓其可以隨視窗調整）
        right_widget = QWidget()
        right_widget.setMinimumWidth(400)
        right_widget.setLayout(right_layout)
        
        # 根據顯示模式創建不同的面板
        if self.display_mode == "RULA":
            # RULA 評估模式
            self.left_group = ScorePanel("左側 RULA 評估")
            self.left_group.setMinimumHeight(280)
            right_layout.addWidget(self.left_group, stretch=1)  # 給予伸縮權重
            
            self.right_group = ScorePanel("右側 RULA 評估")
            self.right_group.setMinimumHeight(280)
            right_layout.addWidget(self.right_group, stretch=1)  # 給予伸縮權重
        else:
            # 坐標顯示模式
            self.coordinates_group = CoordinatesPanel("關鍵點坐標")
            right_layout.addWidget(self.coordinates_group, stretch=1)  # 給予伸縮權重
        
        main_layout.addWidget(right_widget, stretch=2)  # 右側佔2份
        
    def start_detection(self):
        """開始辨識"""
        if self.camera_mode == "KINECT":
            # 使用 Azure Kinect（含 Body Tracking）
            if not KINECT_AVAILABLE:
                self.on_error("Azure Kinect 不可用，請檢查 SDK 安裝")
                return
            
            self.kinect_handler = KinectHandler()
            self.kinect_handler.frame_ready.connect(self.on_kinect_frame_ready)
            self.kinect_handler.error_occurred.connect(self.on_error)
            self.kinect_handler.start()
        elif self.camera_mode == "KINECT_RGB":
            # 使用 Kinect RGB 相機 + MediaPipe
            if not KINECT_RGB_AVAILABLE:
                self.on_error("Kinect RGB 不可用，請檢查 SDK 安裝")
                return
            
            self.kinect_rgb_handler = KinectRGBHandler()
            self.kinect_rgb_handler.frame_ready.connect(self.on_frame_ready)
            self.kinect_rgb_handler.error_occurred.connect(self.on_error)
            self.kinect_rgb_handler.start()
        else:  # self.camera_mode == "WEBCAM"
            # 使用攝像頭 + MediaPipe
            self.camera_handler = CameraHandler(camera_index=0)
            self.camera_handler.frame_ready.connect(self.on_frame_ready)
            self.camera_handler.error_occurred.connect(self.on_error)
            self.camera_handler.start()
        
        # 重置暫停狀態和 FPS 計數器
        self.is_paused = False
        self.pause_button.setText("暫停")
        self.fps_counter = 0
        self.fps_timer = cv2.getTickCount()
        
        # 更新按鈕狀態
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.record_button.setEnabled(True)
    
    def stop_detection(self):
        """停止辨識"""
        # 停止攝像頭
        if self.camera_handler:
            try:
                self.camera_handler.frame_ready.disconnect()
                self.camera_handler.error_occurred.disconnect()
            except:
                pass
            self.camera_handler.stop()
            self.camera_handler = None
        
        # 停止 Kinect
        if self.kinect_handler:
            try:
                self.kinect_handler.frame_ready.disconnect()
                self.kinect_handler.error_occurred.disconnect()
            except:
                pass
            self.kinect_handler.stop()
            self.kinect_handler = None
        
        # 停止 Kinect RGB
        if self.kinect_rgb_handler:
            try:
                self.kinect_rgb_handler.frame_ready.disconnect()
                self.kinect_rgb_handler.error_occurred.disconnect()
            except:
                pass
            self.kinect_rgb_handler.stop()
            self.kinect_rgb_handler = None
        
        # 重置計數器和暫停狀態
        self.frame_counter = 0
        self.fps_counter = 0
        self.prev_left = None
        self.prev_right = None
        self.is_paused = False
        self.pause_button.setText("暫停")
        
        # 停止倒數計時器
        if self.countdown_active:
            self.countdown_timer.stop()
            self.countdown_active = False
        
        # 停止錄影
        if self.is_recording:
            self.stop_recording()
        
        # 重置 FPS 顯示
        self.current_fps = 0.0
        self.fps_label.setText("FPS: 0.0")
        
        # 重置顯示
        self.video_label.setText("已停止")
        
        # 根據顯示模式重置面板
        if self.display_mode == "RULA":
            self.left_group.reset_panel()
            self.right_group.reset_panel()
        else:
            self.coordinates_group.reset_panel()
        
        # 更新按鈕狀態
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.record_button.setEnabled(False)
    
    def on_frame_ready(self, frame):
        """
        處理新影像幀
        
        Args:
            frame: RGB 格式的影像 (numpy array)
        """
        # 如果暫停，則不更新顯示
        if self.is_paused:
            return
        
        self.frame_counter += 1
        
        # 每幀都進行骨架辨識（保持骨架顯示流暢）
        detected = self.pose_detector.process_frame(frame)
        
        # 計算 FPS（包含骨架偵測時間）
        self.fps_counter += 1
        if self.fps_counter >= 30:
            current_time = cv2.getTickCount()
            elapsed = (current_time - self.fps_timer) / cv2.getTickFrequency()
            fps = self.fps_counter / elapsed
            self.on_fps_updated(fps)
            
            self.fps_counter = 0
            self.fps_timer = current_time
        
        if detected:
            # 繪製骨架（每幀都繪製，不閃爍）
            annotated = self.pose_detector.draw_landmarks(frame)
            
            # 根據顯示模式更新面板
            if self.display_mode == "RULA":
                # 只在特定幀才計算 RULA（降低計算負擔）
                if self.frame_counter % self.rula_calc_every_n_frames == 0:
                    # 取得關鍵點並計算 RULA
                    landmarks = self.pose_detector.get_landmarks_array()
                    rula_left, rula_right = angle_calc(landmarks, self.prev_left, self.prev_right)
                    
                    # 儲存為下一幀的參考
                    self.prev_left = rula_left
                    self.prev_right = rula_right
                    
                    # 更新顯示
                    self.left_group.update_score_panel(rula_left)
                    self.right_group.update_score_panel(rula_right)
                    
                    # 如果正在錄影，記錄分數
                    if self.is_recording:
                        self.record_rula_scores(rula_left, rula_right)
            else:
                # 坐標顯示模式 - 每幀更新
                landmarks = self.pose_detector.get_landmarks_array()
                if landmarks:
                    self.coordinates_group.update_coordinates(landmarks)
        else:
            annotated = frame
        
        # 保存繪製骨架後的影像（用於保存功能）
        self.current_frame = annotated
        
        # 如果正在錄影，寫入影像幀
        if self.is_recording and self.video_writer is not None:
            # 轉換為 BGR 格式（OpenCV VideoWriter 需要）
            frame_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            self.video_writer.write(frame_bgr)
            self.recording_frame_count += 1
        
        # 如果正在倒數，在畫面上繪製倒數數字
        if self.countdown_active and self.countdown_value > 0:
            annotated = self.draw_countdown_on_frame(annotated)
        
        # 如果正在錄影，在畫面上繪製錄影指示
        if self.is_recording:
            annotated = self.draw_recording_indicator(annotated)
        
        # 顯示影像
        FrameRenderer.display_frame(self.video_label, annotated)
    
    def on_kinect_frame_ready(self, frame, pose):
        """
        處理 Kinect 影像幀和骨架數據
        
        Args:
            frame: RGB 格式的影像 (numpy array，已繪製骨架)
            pose: 骨架關鍵點列表 (MediaPipe 格式) 或 None
        """
        # 如果暫停，則不更新顯示
        if self.is_paused:
            return
        
        self.current_frame = frame
        self.frame_counter += 1
        
        # 計算 FPS（反映完整的處理速度）
        self.fps_counter += 1
        if self.fps_counter >= 30:
            current_time = cv2.getTickCount()
            elapsed = (current_time - self.fps_timer) / cv2.getTickFrequency()
            fps = self.fps_counter / elapsed
            self.on_fps_updated(fps)
            
            self.fps_counter = 0
            self.fps_timer = current_time
        
        # Kinect 已經在 frame 上繪製了骨架，直接使用
        annotated = frame
        
        # 如果有骨架數據，進行 RULA 計算（檢查 pose 列表是否非空）
        if pose:
            # 根據顯示模式更新面板
            if self.display_mode == "RULA":
                # 只在特定幀才計算 RULA（降低計算負擔）
                if self.frame_counter % self.rula_calc_every_n_frames == 0:
                    rula_left, rula_right = angle_calc(pose, self.prev_left, self.prev_right)
                    
                    # 儲存為下一幀的參考
                    self.prev_left = rula_left
                    self.prev_right = rula_right
                    
                    # 更新顯示
                    self.left_group.update_score_panel(rula_left)
                    self.right_group.update_score_panel(rula_right)
                    
                    # 如果正在錄影，記錄分數
                    if self.is_recording:
                        self.record_rula_scores(rula_left, rula_right)
            else:
                # 坐標顯示模式 - 每幀更新
                self.coordinates_group.update_coordinates(pose)
        
        # 如果正在錄影，寫入影像幀
        if self.is_recording and self.video_writer is not None:
            # 轉換為 BGR 格式（OpenCV VideoWriter 需要）
            frame_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            self.video_writer.write(frame_bgr)
            self.recording_frame_count += 1
        
        # 如果正在倒數，在畫面上繪製倒數數字
        if self.countdown_active and self.countdown_value > 0:
            annotated = self.draw_countdown_on_frame(annotated)
        
        # 如果正在錄影，在畫面上繪製錄影指示
        if self.is_recording:
            annotated = self.draw_recording_indicator(annotated)
        
        # 顯示影像
        FrameRenderer.display_frame(self.video_label, annotated)
    
    def update_score_panel(self, panel, rula_data):
        """
        更新分數面板
        
        Args:
            panel: ScorePanel
            rula_data: RULA 計算結果字典
        """
        panel.update_score_panel(rula_data)
    
    def display_frame(self, frame):
        """
        顯示影像幀
        
        Args:
            frame: RGB 格式的影像
        """
        FrameRenderer.display_frame(self.video_label, frame)
    
    def on_error(self, error_msg):
        """處理錯誤"""
        # 在視窗上顯示錯誤
        self.video_label.setText(f"錯誤: {error_msg}")
        
        # 彈出錯誤對話框
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("錯誤")
        
        # 設置主要文本
        if "Kinect" in error_msg or "連接" in error_msg:
            msg_box.setText("Azure Kinect 連接失敗")
        else:
            msg_box.setText("發生錯誤")
        
        # 設置詳細信息（不使用 DetailedText 避免出現細節按鈕）
        msg_box.setInformativeText(error_msg)
        
        # 設置樣式以確保文字可見
        msg_box.setStyleSheet(ERROR_MESSAGEBOX_STYLE)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
        # 停止檢測
        self.stop_detection()
    
    def on_fps_updated(self, fps):
        """更新 FPS 顯示"""
        self.current_fps = fps
        self.fps_label.setText(f"FPS: {fps:.1f}")
    
    def toggle_pause(self):
        """切換暫停/繼續"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.setText("繼續")
        else:
            self.pause_button.setText("暫停")
    
    def save_snapshot(self):
        """開始倒數3秒後保存當前畫面和分數"""
        if self.current_frame is None:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("警告")
            msg_box.setText("沒有可保存的畫面")
            msg_box.setStyleSheet(MESSAGEBOX_WIDE_STYLE)
            msg_box.exec()
            return
        
        # 如果已經在倒數中，忽略
        if self.countdown_active:
            return
        
        # 開始倒數
        self.countdown_active = True
        self.countdown_value = 3
        self.countdown_timer.start(1000)  # 每秒更新一次
    
    def update_countdown(self):
        """更新倒數計時器"""
        if self.countdown_value > 0:
            # 繼續倒數
            self.countdown_value -= 1
        else:
            # 倒數結束，執行保存
            self.countdown_timer.stop()
            self.countdown_active = False
            self.perform_save()
    
    def perform_save(self):
        """執行實際的保存操作"""
        if self.current_frame is None:
            return
        
        try:
            # 根據顯示模式處理保存
            if self.display_mode == "RULA":
                success, message = SnapshotManager.save_rula_snapshot(
                    self.current_frame, self.left_group, self.right_group, self
                )
            else:
                # COORDINATES 模式：只保存圖片和坐標文本
                landmarks = self.pose_detector.get_landmarks_array() if self.pose_detector else None
                success, message = SnapshotManager.save_coordinates_snapshot(
                    self.current_frame, landmarks, self
                )
            
            if success:
                # 顯示成功訊息
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("保存成功")
                msg_box.setText("文件已成功保存！")
                msg_box.setInformativeText(message)
                msg_box.setStyleSheet(SUCCESS_MESSAGEBOX_STYLE)
                msg_box.exec()
            else:
                # 顯示錯誤訊息
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("錯誤")
                msg_box.setText("保存失敗")
                msg_box.setInformativeText(message)
                msg_box.setStyleSheet(MESSAGEBOX_WIDE_STYLE)
                msg_box.exec()
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("錯誤")
            msg_box.setText("保存失敗")
            msg_box.setInformativeText(str(e))
            msg_box.setStyleSheet(MESSAGEBOX_WIDE_STYLE)
            msg_box.exec()
    
    def draw_countdown_on_frame(self, frame):
        """在影像上繪製倒數數字
        
        Args:
            frame: RGB 格式的影像 (numpy array)
            
        Returns:
            繪製倒數數字後的影像副本
        """
        frame_copy = frame.copy()
        h, w = frame_copy.shape[:2]
        
        # 計算文字大小和位置
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 8
        thickness = 15
        text = str(self.countdown_value)
        
        # 獲取文字大小
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 居中位置
        x = (w - text_width) // 2
        y = (h + text_height) // 2
        
        # 繪製半透明背景
        overlay = frame_copy.copy()
        cv2.circle(overlay, (w // 2, h // 2), 150, (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame_copy, 0.4, 0, frame_copy)
        
        # 繪製倒數數字（黃色）
        cv2.putText(frame_copy, text, (x, y), font, font_scale, (0, 255, 255), thickness)
        
        return frame_copy
    
    def show_config_dialog(self):
        """顯示參數設定對話框"""
        dialog = RULAConfigDialog(self)
        dialog.exec()
    
    def toggle_recording(self):
        """切換錄影狀態"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """開始錄影"""
        if self.current_frame is None:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("警告")
            msg_box.setText("沒有可錄製的畫面")
            msg_box.setStyleSheet("QMessageBox {background-color: white;} QLabel {color: black; font-size: 12px;} QPushButton {color: black; background-color: #e0e0e0; border: 1px solid #999; padding: 5px 15px;}")
            msg_box.exec()
            return
        
        try:
            # 確保目錄存在
            from .components import SnapshotManager
            SnapshotManager.ensure_directory_exists(SnapshotManager.RECORDING_DIR)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.recording_filename = timestamp
            video_path = os.path.join(SnapshotManager.RECORDING_DIR, f"recording_{timestamp}.mp4")
            
            # 獲取影像尺寸
            h, w = self.current_frame.shape[:2]
            
            # 設定編解碼器和創建 VideoWriter (統一使用 MP4 格式)
            fps = max(self.current_fps, 20.0) if self.current_fps > 0 else 20.0
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 格式
            self.video_writer = cv2.VideoWriter(video_path, fourcc, fps, (w, h))
            
            if not self.video_writer.isOpened():
                error_msg = f"無法創建影片文件\n\n"
                error_msg += f"嘗試的路徑: {video_path}\n"
                error_msg += f"影像尺寸: {w}x{h}\n"
                error_msg += f"FPS: {fps}\n"
                error_msg += f"\n請確認:\n"
                error_msg += f"1. OpenCV 已正確安裝\n"
                error_msg += f"2. 編解碼器可用\n"
                error_msg += f"3. 有磁碟寫入權限"
                raise Exception(error_msg)
            
            # 設定錄影狀態
            self.is_recording = True
            self.recording_start_time = datetime.now()
            self.recording_frame_count = 0
            self.rula_records = []
            self.recording_video_path = video_path  # 保存實際視頻路徑
            
            # 更新按鈕樣式和文字
            from .styles import RECORD_BUTTON_STYLE
            self.record_button.setStyleSheet(RECORD_BUTTON_STYLE)
            self.record_button.setText("⏹ 停止")
            
            # 禁用開始/停止按鈕（錄影期間不能停止檢測）
            self.stop_button.setEnabled(False)
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            error_msg = f"無法開始錄影:\n\n{str(e)}\n\n詳細錯誤:\n{error_detail}"
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("錯誤")
            msg_box.setText(error_msg)
            msg_box.setStyleSheet("QMessageBox {background-color: white;} QLabel {color: black; font-size: 11px; min-width: 400px;} QPushButton {color: black; background-color: #e0e0e0; border: 1px solid #999; padding: 5px 15px;}")
            msg_box.exec()
    
    def stop_recording(self):
        """停止錄影並保存分數記錄"""
        if not self.is_recording:
            return
        
        try:
            # 關閉 VideoWriter
            if self.video_writer is not None:
                self.video_writer.release()
                self.video_writer = None
            
            # 保存 RULA 分數記錄（只在 RULA 模式下）
            if self.display_mode == "RULA" and self.rula_records:
                from .components import SnapshotManager
                txt_path = os.path.join(
                    SnapshotManager.RECORDING_DIR, 
                    f"recording_{self.recording_filename}.txt"
                )
                self.save_rula_records(txt_path)
            
            # 顯示錄影完成訊息
            duration = (datetime.now() - self.recording_start_time).total_seconds()
            
            msg_text = f"錄影已完成！\n\n"
            msg_text += f"影片: {self.recording_video_path}\n"
            msg_text += f"時長: {duration:.1f} 秒\n"
            msg_text += f"幀數: {self.recording_frame_count}\n"
            
            if self.display_mode == "RULA" and self.rula_records:
                txt_path = os.path.join(
                    SnapshotManager.RECORDING_DIR, 
                    f"recording_{self.recording_filename}.txt"
                )
                msg_text += f"分數記錄: {txt_path}"
            
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("錄影完成")
            msg_box.setText(msg_text)
            msg_box.setStyleSheet("QMessageBox {background-color: white;} QLabel {color: black; font-size: 12px;} QPushButton {color: black; background-color: #e0e0e0; border: 1px solid #999; padding: 5px 15px;}")
            msg_box.exec()
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("錯誤")
            msg_box.setText(f"停止錄影時發生錯誤:\n{str(e)}")
            msg_box.setStyleSheet("QMessageBox {background-color: white;} QLabel {color: black; font-size: 12px;} QPushButton {color: black; background-color: #e0e0e0; border: 1px solid #999; padding: 5px 15px;}")
            msg_box.exec()
        finally:
            # 重置錄影狀態
            self.is_recording = False
            self.recording_start_time = None
            self.recording_frame_count = 0
            self.rula_records = []
            self.recording_filename = None
            self.recording_video_path = None
            
            # 恢復按鈕樣式和文字
            from .styles import RECORD_BUTTON_READY_STYLE
            self.record_button.setStyleSheet(RECORD_BUTTON_READY_STYLE)
            self.record_button.setText("⏺ 錄影")
            
            # 重新啟用停止按鈕
            self.stop_button.setEnabled(True)
    
    def record_rula_scores(self, rula_left, rula_right):
        """記錄當前幀的 RULA 分數"""
        if not self.is_recording:
            return
        
        elapsed = (datetime.now() - self.recording_start_time).total_seconds()
        
        record = {
            'timestamp': elapsed,
            'frame': self.recording_frame_count,
            'left': rula_left,
            'right': rula_right
        }
        self.rula_records.append(record)
    
    def save_rula_records(self, filepath):
        """保存 RULA 分數記錄到文本文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("RULA 錄影分數記錄\n")
                f.write("=" * 80 + "\n")
                f.write(f"錄影時間: {self.recording_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"總時長: {(datetime.now() - self.recording_start_time).total_seconds():.1f} 秒\n")
                f.write(f"總幀數: {self.recording_frame_count}\n")
                f.write(f"記錄數量: {len(self.rula_records)}\n")
                f.write("=" * 80 + "\n\n")
                
                # 寫入每條記錄
                for record in self.rula_records:
                    f.write(f"\n--- 時間: {record['timestamp']:.2f}s | 幀: {record['frame']} ---\n")
                    f.write("\n【左側】\n")
                    self._write_rula_data(f, record['left'])
                    f.write("\n【右側】\n")
                    self._write_rula_data(f, record['right'])
                    f.write("\n" + "-" * 80 + "\n")
                
                # 統計資訊
                f.write("\n" + "=" * 80 + "\n")
                f.write("統計資訊\n")
                f.write("=" * 80 + "\n")
                
                if self.rula_records:
                    left_scores = [r['left'].get('score', 0) for r in self.rula_records if r['left'].get('score') != '--']
                    right_scores = [r['right'].get('score', 0) for r in self.rula_records if r['right'].get('score') != '--']
                    
                    if left_scores:
                        f.write(f"\n左側 RULA 分數:\n")
                        f.write(f"  平均: {sum(left_scores)/len(left_scores):.2f}\n")
                        f.write(f"  最小: {min(left_scores)}\n")
                        f.write(f"  最大: {max(left_scores)}\n")
                    
                    if right_scores:
                        f.write(f"\n右側 RULA 分數:\n")
                        f.write(f"  平均: {sum(right_scores)/len(right_scores):.2f}\n")
                        f.write(f"  最小: {min(right_scores)}\n")
                        f.write(f"  最大: {max(right_scores)}\n")
        
        except Exception as e:
            print(f"保存分數記錄失敗: {e}")
    
    def _write_rula_data(self, file, rula_data):
        """寫入單側 RULA 數據到文件"""
        if not rula_data:
            file.write("  無數據\n")
            return
        
        file.write(f"  上臂角度: {rula_data.get('upper_arm_angle', 'NULL')}° (分數: {rula_data.get('upper_arm_score', '--')})\n")
        file.write(f"  前臂角度: {rula_data.get('lower_arm_angle', 'NULL')}° (分數: {rula_data.get('lower_arm_score', '--')})\n")
        file.write(f"  手腕角度: {rula_data.get('wrist_angle', 'NULL')}° (分數: {rula_data.get('wrist_score', '--')})\n")
        file.write(f"  頸部角度: {rula_data.get('neck_angle', 'NULL')}° (分數: {rula_data.get('neck_score', '--')})\n")
        file.write(f"  軀幹角度: {rula_data.get('trunk_angle', 'NULL')}° (分數: {rula_data.get('trunk_score', '--')})\n")
        file.write(f"  Table A: {rula_data.get('wrist_and_arm_score', '--')}\n")
        file.write(f"  Table B: {rula_data.get('neck_trunk_leg_score', '--')}\n")
        file.write(f"  Table C (總分): {rula_data.get('score', '--')}\n")
    
    def draw_recording_indicator(self, frame):
        """在影像上繪製錄影指示（紅點+時間）"""
        frame_copy = frame.copy()
        h, w = frame_copy.shape[:2]
        
        # 計算錄影時長
        if self.recording_start_time:
            elapsed = (datetime.now() - self.recording_start_time).total_seconds()
            time_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
        else:
            time_str = "00:00"
        
        # 繪製半透明背景
        overlay = frame_copy.copy()
        cv2.rectangle(overlay, (w - 150, 10), (w - 10, 50), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame_copy, 0.4, 0, frame_copy)
        
        # 繪製紅色圓點（閃爍效果）
        import time
        if int(time.time() * 2) % 2 == 0:  # 每0.5秒閃爍一次
            cv2.circle(frame_copy, (w - 130, 30), 8, (0, 0, 255), -1)
        
        # 繪製錄影時間
        cv2.putText(frame_copy, time_str, (w - 110, 38), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame_copy
    
    def closeEvent(self, event):
        """視窗關閉事件"""
        # 停止錄影
        if self.is_recording:
            self.stop_recording()
        
        # 停止攝像頭
        if self.camera_handler:
            self.camera_handler.stop()
        
        # 停止 Kinect
        if self.kinect_handler:
            self.kinect_handler.stop()
        
        # 停止 Kinect RGB
        if self.kinect_rgb_handler:
            self.kinect_rgb_handler.stop()
        
        # 關閉 MediaPipe pose detector
        if self.pose_detector:
            self.pose_detector.close()
        
        event.accept()
