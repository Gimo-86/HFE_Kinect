"""
主視窗 UI
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGroupBox, QGridLayout, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
import numpy as np

from core.camera_handler import CameraHandler
from core.pose_detector import PoseDetector
from core import angle_calc, get_best_rula_score
from core.config import RULA_CONFIG, USE_KINECT

# 根據配置選擇性導入 Kinect
if USE_KINECT:
    try:
        from core.kinect_handler import KinectHandler
        KINECT_AVAILABLE = True
    except Exception as e:
        print(f"警告: 無法載入 Kinect 模組: {e}")
        KINECT_AVAILABLE = False
else:
    KINECT_AVAILABLE = False


class MainWindow(QMainWindow):
    """
    RULA 即時評估主視窗
    """
    
    def __init__(self):
        super().__init__()
        
        # 根據配置設定視窗標題
        source_type = "Azure Kinect" if USE_KINECT else "攝像頭"
        self.setWindowTitle(f"RULA 即時評估系統 - {source_type}")
        self.setGeometry(100, 100, 1400, 700)  # 加寬視窗
        
        # 核心元件
        self.camera_handler = None
        self.kinect_handler = None
        self.pose_detector = None if USE_KINECT else PoseDetector()
        
        # RULA 計算用的前一幀資料
        self.prev_left = None
        self.prev_right = None
        
        # 當前影像
        self.current_frame = None
        
        # FPS 資訊
        self.current_fps = 0.0
        
        # 暫停狀態
        self.is_paused = False
        
        # 處理計數器（降低 RULA 計算頻率）
        self.frame_counter = 0
        self.rula_calc_every_n_frames = 5  # 每5幀才計算一次 RULA（降低計算負擔）
        
        # 最後的骨架繪製結果（用於未處理的幀）
        self.last_annotated_frame = None
        
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
        
        # 左側身體評估
        self.left_group = self.create_score_panel("左側 RULA 評估")
        self.left_group.setMinimumHeight(280)  # 確保足夠高度
        right_layout.addWidget(self.left_group)
        
        # 右側身體評估
        self.right_group = self.create_score_panel("右側 RULA 評估")
        self.right_group.setMinimumHeight(280)  # 確保足夠高度
        right_layout.addWidget(self.right_group)
        
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
    
    def start_detection(self):
        """開始辨識"""
        if USE_KINECT:
            # 使用 Azure Kinect
            if not KINECT_AVAILABLE:
                self.on_error("Azure Kinect 不可用，請檢查 SDK 安裝")
                return
            
            self.kinect_handler = KinectHandler()
            self.kinect_handler.frame_ready.connect(self.on_kinect_frame_ready)
            self.kinect_handler.error_occurred.connect(self.on_error)
            self.kinect_handler.fps_updated.connect(self.on_fps_updated)
            self.kinect_handler.start()
        else:
            # 使用攝像頭 + MediaPipe
            self.camera_handler = CameraHandler(camera_index=0)
            self.camera_handler.frame_ready.connect(self.on_frame_ready)
            self.camera_handler.error_occurred.connect(self.on_error)
            self.camera_handler.fps_updated.connect(self.on_fps_updated)
            self.camera_handler.start()
        
        # 重置暫停狀態
        self.is_paused = False
        self.pause_button.setText("暫停")
        
        # 更新按鈕狀態
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.pause_button.setEnabled(True)
    
    def stop_detection(self):
        """停止辨識"""
        # 停止攝像頭
        if self.camera_handler:
            try:
                self.camera_handler.frame_ready.disconnect()
                self.camera_handler.error_occurred.disconnect()
                self.camera_handler.fps_updated.disconnect()
            except:
                pass
            self.camera_handler.stop()
            self.camera_handler = None
        
        # 停止 Kinect
        if self.kinect_handler:
            try:
                self.kinect_handler.frame_ready.disconnect()
                self.kinect_handler.error_occurred.disconnect()
                self.kinect_handler.fps_updated.disconnect()
            except:
                pass
            self.kinect_handler.stop()
            self.kinect_handler = None
        
        # 重置計數器和暫停狀態
        self.frame_counter = 0
        self.prev_left = None
        self.prev_right = None
        self.is_paused = False
        self.pause_button.setText("暫停")
        
        # 重置顯示
        self.video_label.setText("已停止")
        self.update_score_panel(self.left_group, {})
        self.update_score_panel(self.right_group, {})
        
        # 更新按鈕狀態
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.pause_button.setEnabled(False)
    
    def on_frame_ready(self, frame):
        """
        處理新影像幀
        
        Args:
            frame: RGB 格式的影像 (numpy array)
        """
        # 如果暫停，則不更新顯示
        if self.is_paused:
            return
        
        self.current_frame = frame
        self.frame_counter += 1
        
        # 每幀都進行骨架辨識（保持骨架顯示流暢）
        detected = self.pose_detector.process_frame(frame)
        
        if detected:
            # 繪製骨架（每幀都繪製，不閃爍）
            annotated = self.pose_detector.draw_landmarks(frame)
            
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
            annotated = frame
        
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
        
        # Kinect 已經在 frame 上繪製了骨架，直接使用
        annotated = frame
        
        # 如果有骨架數據，進行 RULA 計算
        if pose is not None:
            # 只在特定幀才計算 RULA（降低計算負擔）
            if self.frame_counter % self.rula_calc_every_n_frames == 0:
                rula_left, rula_right = angle_calc(pose, self.prev_left, self.prev_right)
                
                # 儲存為下一幀的參考
                self.prev_left = rula_left
                self.prev_right = rula_right
                
                # 更新顯示
                self.update_score_panel(self.left_group, rula_left)
                self.update_score_panel(self.right_group, rula_right)
        
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
        
        # 關閉 MediaPipe pose detector
        if self.pose_detector:
            self.pose_detector.close()
        
        event.accept()
