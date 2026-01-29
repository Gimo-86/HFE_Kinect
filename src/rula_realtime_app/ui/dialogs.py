"""
Dialog windows for RULA application
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QDialogButtonBox, QGridLayout, QPushButton)
from ..core.config import RULA_CONFIG


class RULAConfigDialog(QDialog):
    """Configuration dialog for RULA parameters"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RULA 預設參數設定")
        self.setMinimumSize(400, 350)
        self.setStyleSheet("""
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
        close_button.clicked.connect(self.accept)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)    