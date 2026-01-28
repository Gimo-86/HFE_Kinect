"""
主視窗 UI
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGroupBox, QGridLayout, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
import numpy as np
import cv2
from datetime import datetime
import os

from core.camera_handler import CameraHandler
from core.pose_detector import PoseDetector
from core import angle_calc, get_best_rula_score
from core import config as core_config
from core.config import RULA_CONFIG

# 嘗試導入所有可能的相機模組（動態判斷）
try:
    from core.kinect_handler import KinectHandler
    KINECT_AVAILABLE = True
except Exception as e:
    print(f"警告: 無法載入 Kinect 模組: {e}")
    KINECT_AVAILABLE = False

try:
    from core.kinect_rgb_handler import KinectRGBHandler
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
        
        # 顯示模式 - 從 config 模組動態讀取
        self.display_mode = core_config.DISPLAY_MODE  # "RULA" 或 "COORDINATES"
        
        # 初始化 UI
        self.init_ui()
        
    def init_ui(self):
        """初始化使用者介面"""
        # 設定整體樣式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
            }
            QWidget {
                color: #ecf0f1;
                font-family: "Microsoft JhengHei", "微軟正黑體", Arial;
            }
            QLabel {
                color: #ecf0f1;
            }
        """)
        
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
        self.video_label.setMaximumSize(640, 480)
        self.video_label.setScaledContents(True)
        self.video_label.setStyleSheet("""
            border: 3px solid #3498db;
            border-radius: 10px;
            background-color: #1a1a1a;
            font-size: 16px;
            color: #95a5a6;
        """)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("等待開始...")
        left_layout.addWidget(self.video_label)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("開始")
        self.start_button.clicked.connect(self.start_detection)
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
            }
            QPushButton:pressed {
                background: #229954;
            }
            QPushButton:disabled {
                background: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_detection)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:1 #e74c3c);
            }
            QPushButton:pressed {
                background: #c0392b;
            }
            QPushButton:disabled {
                background: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.stop_button)
        
        self.pause_button = QPushButton("暫停")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setEnabled(False)
        self.pause_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f39c12, stop:1 #e67e22);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f4a742, stop:1 #f39c12);
            }
            QPushButton:pressed {
                background: #e67e22;
            }
            QPushButton:disabled {
                background: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.pause_button)
        
        self.save_button = QPushButton("💾 保存")
        self.save_button.clicked.connect(self.save_snapshot)
        self.save_button.setEnabled(False)
        self.save_button.setToolTip("保存當前畫面和分數")
        self.save_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #16a085, stop:1 #138d75);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1abc9c, stop:1 #16a085);
            }
            QPushButton:pressed {
                background: #138d75;
            }
            QPushButton:disabled {
                background: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 12px 20px;
            background-color: rgba(52, 73, 94, 0.7);
            border-radius: 8px;
            color: #3498db;
        """)
        button_layout.addWidget(self.fps_label)
        
        # 參數設定按鈕（齒輪圖案）
        self.config_button = QPushButton("⚙")
        self.config_button.clicked.connect(self.show_config_dialog)
        self.config_button.setToolTip("RULA 參數設定")
        self.config_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #6c3483);
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
                min-width: 50px;
                max-width: 50px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
            }
            QPushButton:pressed {
                background: #6c3483;
            }
        """)
        button_layout.addWidget(self.config_button)
        
        button_layout.addStretch()
        left_layout.addLayout(button_layout)
        
        main_layout.addLayout(left_layout)
        
        # === 右側：評估面板 ===
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        # 設定右側面板容器的最小寬度
        right_widget = QWidget()
        right_widget.setMinimumWidth(400)
        right_widget.setMaximumWidth(500)  # 限制最大寬度避免過寬
        right_widget.setLayout(right_layout)
        
        # 根據顯示模式創建不同的面板
        if self.display_mode == "RULA":
            # RULA 評估模式
            self.left_group = self.create_score_panel("左側 RULA 評估")
            self.left_group.setMinimumHeight(280)
            right_layout.addWidget(self.left_group)
            
            self.right_group = self.create_score_panel("右側 RULA 評估")
            self.right_group.setMinimumHeight(280)
            right_layout.addWidget(self.right_group)
        else:
            # 坐標顯示模式
            self.coordinates_group = self.create_coordinates_panel("關鍵點坐標")
            right_layout.addWidget(self.coordinates_group)
        
        right_layout.addStretch()
        
        main_layout.addWidget(right_widget)
        
    def create_score_panel(self, title):
        """
        創建分數顯示面板
        
        Args:
            title: 面板標題
            
        Returns:
            QGroupBox: 分數面板
        """
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #3498db;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(44, 62, 80, 0.95), stop:1 rgba(52, 73, 94, 0.95));
                border: 2px solid #3498db;
                border-radius: 12px;
                margin-top: 15px;
                padding: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 15px;
                background-color: #2c3e50;
                border-radius: 6px;
            }
            QLabel {
                color: #ecf0f1;
                background: transparent;
            }
        """)
        
        layout = QGridLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 角度標籤
        row = 0
        labels_data = [
            ("upper_arm", "上臂角度:"),
            ("lower_arm", "前臂角度:"),
            ("wrist", "手腕角度:"),
            ("neck", "頸部角度:"),
            ("trunk", "軀幹角度:"),
        ]
        
        group.angle_labels = {}
        group.part_score_labels = {}
        for key, text in labels_data:
            # 角度標籤
            label = QLabel(text)
            label.setStyleSheet("font-size: 13px; color: #ffffff;")
            value = QLabel("--")
            value.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
            layout.addWidget(label, row, 0)
            layout.addWidget(value, row, 1)
            group.angle_labels[key] = value
            
            # 部位分數標籤
            score_label = QLabel("分數:")
            score_label.setStyleSheet("font-size: 12px; color: #95a5a6;")
            score_value = QLabel("--")
            score_value.setStyleSheet("font-size: 13px; font-weight: bold; color: #f39c12;")
            layout.addWidget(score_label, row, 2)
            layout.addWidget(score_value, row, 3)
            group.part_score_labels[key] = score_value
            
            row += 1
        
        # 分隔線
        separator = QLabel()
        separator.setStyleSheet("""
            border: none;
            border-top: 2px solid rgba(52, 152, 219, 0.3);
            margin: 10px 0;
        """)
        separator.setMaximumHeight(10)
        layout.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # RULA 分數
        score_data = [
            ("table_a", "Table A 分數:"),
            ("table_b", "Table B 分數:"),
            ("table_c", "Table C 分數:"),
        ]
        
        group.score_labels = {}
        for key, text in score_data:
            label = QLabel(text)
            label.setStyleSheet("font-size: 13px; color: #3498db; font-weight: bold;")
            value = QLabel("--")
            value.setStyleSheet("font-size: 14px; font-weight: bold; color: #ecf0f1;")
            layout.addWidget(label, row, 0)
            layout.addWidget(value, row, 1)
            group.score_labels[key] = value
            row += 1
        
        group.setLayout(layout)
        return group
    
    def create_coordinates_panel(self, title):
        """
        創建坐標顯示面板
        
        Args:
            title: 面板標題
            
        Returns:
            QGroupBox: 坐標顯示面板
        """
        from PyQt6.QtWidgets import QScrollArea, QTextEdit
        
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #3498db;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(44, 62, 80, 0.95), stop:1 rgba(52, 73, 94, 0.95));
                border: 2px solid #3498db;
                border-radius: 12px;
                margin-top: 15px;
                padding: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 15px;
                background-color: #2c3e50;
                border-radius: 6px;
            }
            QTextEdit {
                background-color: rgba(26, 26, 26, 0.8);
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 5px;
                font-family: "Courier New", monospace;
                font-size: 11px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 使用 QTextEdit 顯示坐標信息
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMinimumHeight(600)
        text_edit.setText("等待骨架數據...")
        
        layout.addWidget(text_edit)
        group.setLayout(layout)
        
        # 保存 text_edit 引用以便後續更新
        group.text_edit = text_edit
        
        return group
    
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
        
        # 重置 FPS 顯示
        self.current_fps = 0.0
        self.fps_label.setText("FPS: 0.0")
        
        # 重置顯示
        self.video_label.setText("已停止")
        
        # 根據顯示模式重置面板
        if self.display_mode == "RULA":
            self.update_score_panel(self.left_group, {})
            self.update_score_panel(self.right_group, {})
        else:
            self.coordinates_group.text_edit.setPlainText("等待骨架數據...")
        
        # 更新按鈕狀態
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.save_button.setEnabled(False)
    
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
                    self.update_score_panel(self.left_group, rula_left)
                    self.update_score_panel(self.right_group, rula_right)
            else:
                # 坐標顯示模式 - 每幀更新
                landmarks = self.pose_detector.get_landmarks_array()
                if landmarks:
                    self.update_coordinates_panel(landmarks)
        else:
            annotated = frame
        
        # 保存繪製骨架後的影像（用於保存功能）
        self.current_frame = annotated
        
        # 顯示影像
        self.display_frame(annotated)
    
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
                    self.update_score_panel(self.left_group, rula_left)
                    self.update_score_panel(self.right_group, rula_right)
            else:
                # 坐標顯示模式 - 每幀更新
                self.update_coordinates_panel(pose)
        
        # 顯示影像
        self.display_frame(annotated)
    
    def update_score_panel(self, panel, rula_data):
        """
        更新分數面板
        
        Args:
            panel: QGroupBox 面板
            rula_data: RULA 計算結果字典
        """
        # 更新角度
        angle_keys = {
            'upper_arm': 'upper_arm_angle',
            'lower_arm': 'lower_arm_angle',
            'wrist': 'wrist_angle',
            'neck': 'neck_angle',
            'trunk': 'trunk_angle',
        }
        
        # 部位分數對應鍵
        score_keys = {
            'upper_arm': 'upper_arm_score',
            'lower_arm': 'lower_arm_score',
            'wrist': 'wrist_score',
            'neck': 'neck_score',
            'trunk': 'trunk_score',
        }
        
        for key, data_key in angle_keys.items():
            # 更新角度
            value = rula_data.get(data_key, 'NULL')
            if value != 'NULL':
                panel.angle_labels[key].setText(f"{value}°")
            else:
                panel.angle_labels[key].setText("--")
            
            # 更新部位分數
            score_value = rula_data.get(score_keys[key], '--')
            panel.part_score_labels[key].setText(str(score_value))
        
        # 更新分數
        table_a = rula_data.get('wrist_and_arm_score', '--')
        table_b = rula_data.get('neck_trunk_leg_score', '--')
        table_c = rula_data.get('score', '--')
        
        panel.score_labels['table_a'].setText(str(table_a))
        panel.score_labels['table_b'].setText(str(table_b))
        panel.score_labels['table_c'].setText(str(table_c))
    
    def update_coordinates_panel(self, landmarks):
        """
        更新坐標顯示面板 - 只顯示用於 RULA 角度計算的關鍵點
        
        Args:
            landmarks: 骨架關鍵點列表 [[x, y, z, visibility], ...]
        """
        # 只顯示用於 RULA 計算的關鍵點
        key_points = {
            0: "Nose",
            11: "Left Shoulder",
            12: "Right Shoulder",
            13: "Left Elbow",
            14: "Right Elbow",
            15: "Left Wrist",
            16: "Right Wrist",
            23: "Left Hip",
            24: "Right Hip",
        }
        
        # 構建顯示文本
        text_lines = []
        
        for idx, name in key_points.items():
            if idx < len(landmarks):
                lm = landmarks[idx]
                x, y, z, vis = lm[0], lm[1], lm[2], lm[3]
                text_lines.append(f"【{idx:2d}】 {name:20s}")
                text_lines.append(f"      X: {x:7.4f}  Y: {y:7.4f}  Z: {z:7.4f}")
                text_lines.append(f"      Visibility: {vis:.4f}")
                text_lines.append("")
        
        display_text = "\n".join(text_lines)
        
        # 更新 QTextEdit
        self.coordinates_group.text_edit.setPlainText(display_text)
    
    def display_frame(self, frame):
        """
        顯示影像幀
        
        Args:
            frame: RGB 格式的影像
        """
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.video_label.setPixmap(pixmap)
    
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
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: black;
                font-size: 11px;
            }
            QPushButton {
                color: black;
                background-color: #e0e0e0;
                border: 1px solid #999;
                padding: 5px 15px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        
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
        """保存當前畫面和分數"""
        if self.current_frame is None:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("警告")
            msg_box.setText("沒有可保存的畫面")
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QLabel {
                    color: black;
                    font-size: 12px;
                    min-width: 200px;
                }
                QPushButton {
                    color: black;
                    background-color: #e0e0e0;
                    border: 1px solid #999;
                    padding: 5px 15px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
            msg_box.exec()
            return
        
        try:
            # 創建保存目錄
            save_dir = "rula_snapshots"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # 生成文件名（使用時間戳）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 複製當前影像用於保存
            frame_to_save = self.current_frame.copy()
            
            # 根據顯示模式處理保存
            if self.display_mode == "RULA":
                image_path = os.path.join(save_dir, f"rula_{timestamp}.png")
                txt_path = os.path.join(save_dir, f"rula_{timestamp}.txt")
                
                # 在影像上繪製分數資訊
                self.draw_scores_on_frame(frame_to_save)
                
                # 保存影像（OpenCV 使用 BGR 格式）
                cv2.imwrite(image_path, cv2.cvtColor(frame_to_save, cv2.COLOR_RGB2BGR))
                
                # 保存文本資訊
                self.save_scores_to_text(txt_path)
                
                info_text = f"圖片: {image_path}\n文本: {txt_path}"
            else:
                # COORDINATES 模式：只保存圖片和坐標文本
                image_path = os.path.join(save_dir, f"coordinates_{timestamp}.png")
                txt_path = os.path.join(save_dir, f"coordinates_{timestamp}.txt")
                
                # 保存影像（不添加額外資訊）
                cv2.imwrite(image_path, cv2.cvtColor(frame_to_save, cv2.COLOR_RGB2BGR))
                
                # 保存坐標文本
                self.save_coordinates_to_text(txt_path)
                
                info_text = f"圖片: {image_path}\n文本: {txt_path}"
            
            # 顯示成功訊息
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("保存成功")
            msg_box.setText("文件已成功保存！")
            msg_box.setInformativeText(info_text)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QLabel {
                    color: black;
                    font-size: 11px;
                }
                QPushButton {
                    color: black;
                    background-color: #e0e0e0;
                    border: 1px solid #999;
                    padding: 5px 15px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
            msg_box.exec()
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("錯誤")
            msg_box.setText("保存失敗")
            msg_box.setInformativeText(str(e))
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QLabel {
                    color: black;
                    font-size: 12px;
                    min-width: 200px;
                }
                QPushButton {
                    color: black;
                    background-color: #e0e0e0;
                    border: 1px solid #999;
                    padding: 5px 15px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
            msg_box.exec()
    
    def draw_scores_on_frame(self, frame):
        """在影像上繪製分數資訊"""
        height, width = frame.shape[:2]
        
        # 設置文字參數
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0  # 增大字體
        thickness = 2
        line_height = 40  # 增加行高
        y_start = 50
        
        # 計算背景區域大小（正方形區域）
        bg_width = 550  # 固定寬度
        bg_height = 180  # 固定高度
        
        # 創建半透明背景（正方形區域）
        overlay = frame.copy()
        cv2.rectangle(overlay, (15, 15), (15 + bg_width, 15 + bg_height), (44, 62, 80), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        
        # 標題
        cv2.putText(frame, "RULA Evaluation Results", (30, y_start), 
                   font, 1.1, (52, 152, 219), thickness + 1)
        
        # 繪製左側分數
        y = y_start + line_height + 5
        cv2.putText(frame, f"Left Side - Score: {self.get_panel_score(self.left_group)}", 
                   (30, y), font, font_scale, (46, 204, 113), thickness)
        
        # 繪製右側分數
        y += line_height
        cv2.putText(frame, f"Right Side - Score: {self.get_panel_score(self.right_group)}", 
                   (30, y), font, font_scale, (46, 204, 113), thickness)
        
        # 繪製時間戳
        y += line_height - 5
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Time: {timestamp}", (30, y), 
                   font, 0.7, (189, 195, 199), 2)
    
    def get_panel_score(self, panel):
        """從面板獲取總分"""
        try:
            score_text = panel.score_labels['table_c'].text()
            return score_text if score_text != '--' else 'N/A'
        except:
            return 'N/A'
    
    def save_scores_to_text(self, filepath):
        """保存分數到文本文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("RULA 即時評估結果\n")
            f.write("=" * 50 + "\n")
            f.write(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")
            
            # 保存左側數據
            f.write("左側身體評估:\n")
            f.write("-" * 50 + "\n")
            self.write_panel_scores(f, self.left_group)
            f.write("\n")
            
            # 保存右側數據
            f.write("右側身體評估:\n")
            f.write("-" * 50 + "\n")
            self.write_panel_scores(f, self.right_group)
    
    def write_panel_scores(self, file, panel):
        """將面板分數寫入文件"""
        # 寫入角度
        angle_names = {
            'upper_arm': '上臂角度',
            'lower_arm': '前臂角度',
            'wrist': '手腕角度',
            'neck': '頸部角度',
            'trunk': '軀幹角度',
        }
        
        for key, name in angle_names.items():
            angle = panel.angle_labels[key].text()
            score = panel.part_score_labels[key].text()
            file.write(f"  {name}: {angle} (分數: {score})\n")
        
        file.write("\n")
        
        # 寫入總分
        table_a = panel.score_labels['table_a'].text()
        table_b = panel.score_labels['table_b'].text()
        table_c = panel.score_labels['table_c'].text()
        
        file.write(f"  Table A 分數: {table_a}\n")
        file.write(f"  Table B 分數: {table_b}\n")
        file.write(f"  Table C 分數 (總分): {table_c}\n")
    
    def save_coordinates_to_text(self, filepath):
        """保存坐標到文本文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            # 獲取當前顯示的坐標文本
            coord_text = self.coordinates_group.text_edit.toPlainText()
            
            f.write("關鍵點坐標數據\n")
            f.write("=" * 70 + "\n")
            f.write(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            f.write(coord_text)
    
    def show_config_dialog(self):
        """顯示參數設定對話框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("RULA 預設參數設定")
        dialog.setMinimumSize(400, 350)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QLabel {
                color: #ecf0f1;
                font-size: 13px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        title_label = QLabel("目前使用的 RULA 固定參數：")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 參數網格
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        
        params = [
            ("手腕扭轉 (wrist_twist):", RULA_CONFIG['wrist_twist'], "1=中立位置, 2=扭轉"),
            ("腿部姿勢 (legs):", RULA_CONFIG['legs'], "1=平衡站立/坐姿, 2=不平衡"),
            ("肌肉使用-手臂 (muscle_use_a):", RULA_CONFIG['muscle_use_a'], "0=無, 1=靜態/重複"),
            ("肌肉使用-身體 (muscle_use_b):", RULA_CONFIG['muscle_use_b'], "0=無, 1=靜態/重複"),
            ("負荷力量-手臂 (force_load_a):", RULA_CONFIG['force_load_a'], "0=<2kg, 1=2-10kg, 2=>10kg"),
            ("負荷力量-身體 (force_load_b):", RULA_CONFIG['force_load_b'], "0=<2kg, 1=2-10kg, 2=>10kg"),
        ]
        
        row = 0
        for param_name, param_value, param_desc in params:
            # 參數名稱
            name_label = QLabel(param_name)
            name_label.setStyleSheet("font-weight: bold; color: #ecf0f1;")
            grid_layout.addWidget(name_label, row, 0)
            
            # 參數值
            value_label = QLabel(str(param_value))
            value_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f39c12;")
            grid_layout.addWidget(value_label, row, 1)
            row += 1
            
            # 參數說明
            desc_label = QLabel(param_desc)
            desc_label.setStyleSheet("font-size: 11px; color: #95a5a6; margin-bottom: 8px;")
            desc_label.setWordWrap(True)
            grid_layout.addWidget(desc_label, row, 0, 1, 2)
            row += 1
        
        layout.addLayout(grid_layout)
        layout.addStretch()
        
        # 關閉按鈕
        close_button = QPushButton("關閉")
        close_button.clicked.connect(dialog.accept)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def closeEvent(self, event):
        """視窗關閉事件"""
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
