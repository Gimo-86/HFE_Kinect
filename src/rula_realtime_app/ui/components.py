"""
UI Components - Reusable widget classes for RULA application
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, 
                             QGridLayout, QMessageBox, QTextEdit)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
from datetime import datetime
import cv2
import os


from .styles import *


class ScorePanel(QGroupBox):
    """RULA Score Display Panel"""
    
    def __init__(self, title="RULA Score", parent=None):
        """
        創建分數顯示面板

        Args:
            title: 面板標題
            parent: 父級 widget
        """
        super().__init__(title, parent)
        self.setStyleSheet(SCORE_PANEL_STYLE)
        
        self.layout = QGridLayout()
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 角度標籤
        row = 0
        labels_data = [
            ("upper_arm", "上臂角度:"),
            ("lower_arm", "前臂角度:"),
            ("wrist", "手腕角度:"),
            ("neck", "頸部角度:"),
            ("trunk", "軀幹角度:"),
        ]
        
        self.angle_labels = {}
        self.part_score_labels = {}
        for key, text in labels_data:
            # 角度標籤
            label = QLabel(text)
            label.setStyleSheet("font-size: 13px; color: #ffffff;")
            value = QLabel("--")
            value.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
            self.layout.addWidget(label, row, 0)
            self.layout.addWidget(value, row, 1)
            self.angle_labels[key] = value
            
            # 部位分數標籤
            score_label = QLabel("分數:")
            score_label.setStyleSheet("font-size: 12px; color: #95a5a6;")
            score_value = QLabel("--")
            score_value.setStyleSheet("font-size: 13px; font-weight: bold; color: #f39c12;")
            self.layout.addWidget(score_label, row, 2)
            self.layout.addWidget(score_value, row, 3)
            self.part_score_labels[key] = score_value
            
            row += 1
        
        # 分隔線
        separator = QLabel()
        separator.setStyleSheet("""
            border: none;
            border-top: 2px solid rgba(52, 152, 219, 0.3);
            margin: 10px 0;
        """)
        separator.setMaximumHeight(10)
        self.layout.addWidget(separator, row, 0, 1, 2)
        row += 1
        
        # RULA 分數
        score_data = [
            ("table_a", "Table A 分數:"),
            ("table_b", "Table B 分數:"),
            ("table_c", "Table C 分數:"),
        ]
        
        self.score_labels = {}
        for key, text in score_data:
            label = QLabel(text)
            label.setStyleSheet("font-size: 13px; color: #3498db; font-weight: bold;")
            value = QLabel("--")
            value.setStyleSheet("font-size: 14px; font-weight: bold; color: #ecf0f1;")
            self.layout.addWidget(label, row, 0)
            self.layout.addWidget(value, row, 1)
            self.score_labels[key] = value
            row += 1
        
        self.setLayout(self.layout)
    
    def update_score_panel(self, rula_data):
        """
        更新分數面板
        
        Args:
            rula_data: RULA 計算結果字典
        """
        if not rula_data:
            return
            
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
                self.angle_labels[key].setText(f"{value}°")
            else:
                self.angle_labels[key].setText("--")
            
            # 更新部位分數
            score_value = rula_data.get(score_keys[key], '--')
            self.part_score_labels[key].setText(str(score_value))
        
        # 更新分數
        table_a = rula_data.get('wrist_and_arm_score', '--')
        table_b = rula_data.get('neck_trunk_leg_score', '--')
        table_c = rula_data.get('score', '--')
        
        self.score_labels['table_a'].setText(str(table_a))
        self.score_labels['table_b'].setText(str(table_b))
        self.score_labels['table_c'].setText(str(table_c))
    
    def reset_panel(self):
        """重置面板所有值"""
        for key in self.angle_labels:
            self.angle_labels[key].setText("--")
            self.part_score_labels[key].setText("--")
        
        for key in self.score_labels:
            self.score_labels[key].setText("--")
    
    def get_score(self):
        """取得當前面板的總分"""
        try:
            score_text = self.score_labels['table_c'].text()
            return score_text if score_text != '--' else 'N/A'
        except:
            return 'N/A'


class CoordinatesPanel(QGroupBox):
    """Keypoint Coordinates Display Panel"""
    
    def __init__(self, title="Keypoint Coordinates", parent=None):
        """
        創建坐標顯示面板
        
        Args:
            title: 面板標題
            parent: 父級 widget
        """
        super().__init__(title, parent)
        self.setStyleSheet(COORDINATES_PANEL_STYLE)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 使用 QTextEdit 顯示坐標信息
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMinimumHeight(600)
        self.text_edit.setText("等待骨架數據...")
        
        self.layout.addWidget(self.text_edit)
        self.setLayout(self.layout)
    
    def update_coordinates(self, landmarks):
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
        self.text_edit.setPlainText(display_text)
    
    def reset_panel(self):
        """重置面板"""
        self.text_edit.setPlainText("等待骨架數據...")
    
    def get_text(self):
        """取得當前顯示的坐標文本"""
        return self.text_edit.toPlainText()


class FrameRenderer:
    """Handle frame display and rendering"""
    
    @staticmethod
    def display_frame(label, frame):
        """
        顯示影像幀到 QLabel
        
        Args:
            label: QLabel widget 用於顯示圖像
            frame: RGB 格式的影像 (numpy array)
        """
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # 縮放以適應標籤大小，同時保持寬高比
        scaled_pixmap = pixmap.scaled(
            label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)
    
    @staticmethod
    def draw_scores_on_frame(frame, left_score, right_score):
        """
        在影像上繪製分數資訊
        
        Args:
            frame: RGB 格式的影像 (numpy array，會被修改)
            left_score: 左側分數
            right_score: 右側分數
        """
        height, width = frame.shape[:2]
        
        # 設置文字參數
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        line_height = 40
        y_start = 50
        
        # 計算背景區域大小
        bg_width = 550
        bg_height = 180
        
        # 創建半透明背景
        overlay = frame.copy()
        cv2.rectangle(overlay, (15, 15), (15 + bg_width, 15 + bg_height), (44, 62, 80), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        
        # 標題
        cv2.putText(frame, "RULA Evaluation Results", (30, y_start), 
                   font, 1.1, (52, 152, 219), thickness + 1)
        
        # 繪製左側分數
        y = y_start + line_height + 5
        cv2.putText(frame, f"Left Side - Score: {left_score}", 
                   (30, y), font, font_scale, (46, 204, 113), thickness)
        
        # 繪製右側分數
        y += line_height
        cv2.putText(frame, f"Right Side - Score: {right_score}", 
                   (30, y), font, font_scale, (46, 204, 113), thickness)
        
        # 繪製時間戳
        y += line_height - 5
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Time: {timestamp}", (30, y), 
                   font, 0.7, (189, 195, 199), 2)


class SnapshotManager:
    """Handle snapshot saving functionality"""
    
    SNAPSHOT_DIR = "rula_snapshots"
    RECORDING_DIR = "rula_records"
    
    @staticmethod
    def ensure_directory_exists(directory=None):
        """確保保存目錄存在
        
        Args:
            directory: 指定目錄，若為 None 則使用 SNAPSHOT_DIR
        """
        target_dir = directory if directory else SnapshotManager.SNAPSHOT_DIR
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
    
    @staticmethod
    def save_rula_snapshot(frame, left_panel, right_panel, parent_window=None):
        """
        保存 RULA 評估的快照（圖片+文本）
        
        Args:
            frame: RGB 格式的影像 (numpy array)
            left_panel: 左側 ScorePanel
            right_panel: 右側 ScorePanel
            parent_window: 父級窗口（用於消息框）
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            SnapshotManager.ensure_directory_exists()
            
            # 生成文件名（使用時間戳）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(SnapshotManager.SNAPSHOT_DIR, f"rula_{timestamp}.png")
            txt_path = os.path.join(SnapshotManager.SNAPSHOT_DIR, f"rula_{timestamp}.txt")
            
            # 複製當前影像用於保存
            frame_to_save = frame.copy()
            
            # 在影像上繪製分數資訊
            left_score = left_panel.get_score()
            right_score = right_panel.get_score()
            FrameRenderer.draw_scores_on_frame(frame_to_save, left_score, right_score)
            
            # 保存影像（OpenCV 使用 BGR 格式）
            cv2.imwrite(image_path, cv2.cvtColor(frame_to_save, cv2.COLOR_RGB2BGR))
            
            # 保存文本資訊
            SnapshotManager._save_rula_scores_to_text(txt_path, left_panel, right_panel)
            
            info_text = f"圖片: {image_path}\n文本: {txt_path}"
            return True, info_text
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def save_coordinates_snapshot(frame, landmarks, parent_window=None):
        """
        保存坐標顯示的快照（圖片+坐標文本）
        
        Args:
            frame: RGB 格式的影像 (numpy array)
            landmarks: 骨架關鍵點列表
            parent_window: 父級窗口（用於消息框）
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            SnapshotManager.ensure_directory_exists()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(SnapshotManager.SNAPSHOT_DIR, f"coordinates_{timestamp}.png")
            txt_path = os.path.join(SnapshotManager.SNAPSHOT_DIR, f"coordinates_{timestamp}.txt")
            
            # 保存影像
            cv2.imwrite(image_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            # 保存坐標文本
            SnapshotManager._save_coordinates_to_text(txt_path, landmarks)
            
            info_text = f"圖片: {image_path}\n文本: {txt_path}"
            return True, info_text
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def _save_rula_scores_to_text(filepath, left_panel, right_panel):
        """
        保存分數到文本文件
        
        Args:
            filepath: 文件路徑
            left_panel: 左側 ScorePanel
            right_panel: 右側 ScorePanel
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("RULA 即時評估結果\n")
            f.write("=" * 50 + "\n")
            f.write(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")
            
            # 保存左側數據
            f.write("左側身體評估:\n")
            f.write("-" * 50 + "\n")
            SnapshotManager._write_panel_scores(f, left_panel)
            f.write("\n")
            
            # 保存右側數據
            f.write("右側身體評估:\n")
            f.write("-" * 50 + "\n")
            SnapshotManager._write_panel_scores(f, right_panel)
    
    @staticmethod
    def _write_panel_scores(file, panel):
        """
        將面板分數寫入文件
        
        Args:
            file: 文件對象
            panel: ScorePanel
        """
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
    
    @staticmethod
    def _save_coordinates_to_text(filepath, landmarks):
        """
        保存坐標到文本文件
        
        Args:
            filepath: 文件路徑
            landmarks: 骨架關鍵點列表
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("關鍵點坐標數據\n")
            f.write("=" * 70 + "\n")
            f.write(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
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
            
            for idx, name in key_points.items():
                if idx < len(landmarks):
                    lm = landmarks[idx]
                    x, y, z, vis = lm[0], lm[1], lm[2], lm[3]
                    f.write(f"【{idx:2d}】 {name:20s}\n")
                    f.write(f"      X: {x:7.4f}  Y: {y:7.4f}  Z: {z:7.4f}\n")
                    f.write(f"      Visibility: {vis:.4f}\n\n")


