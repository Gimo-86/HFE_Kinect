"""
Dialog windows for RULA application
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QGridLayout, QPushButton)
from ..core import config
from .styles import RULA_CONFIG_DIALOG_STYLE


class RULAConfigDialog(QDialog):
    """Configuration dialog for RULA parameters with dropdown controls"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RULA 預設參數設定")
        self.setMinimumSize(500, 450)
        self.setStyleSheet(RULA_CONFIG_DIALOG_STYLE)
        
        # Store references to combo boxes for retrieval
        self.combos = {}
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        title_label = QLabel("調整 RULA 固定參數：")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 參數網格
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setColumnStretch(0, 2)
        grid_layout.setColumnStretch(1, 1)
        
        # Define parameter options
        param_config = [
            ("wrist_twist", "手腕扭轉 (wrist_twist):", ["1 - 中立位置", "2 - 扭轉"], "1=中立位置, 2=扭轉"),
            ("legs", "腿部姿勢 (legs):", ["1 - 平衡站立/坐姿", "2 - 不平衡"], "1=平衡站立/坐姿, 2=不平衡"),
            ("muscle_use_a", "肌肉使用-手臂 (muscle_use_a):", ["0 - 無", "1 - 靜態/重複"], "0=無, 1=靜態/重複"),
            ("muscle_use_b", "肌肉使用-身體 (muscle_use_b):", ["0 - 無", "1 - 靜態/重複"], "0=無, 1=靜態/重複"),
            ("force_load_a", "負荷力量-手臂 (force_load_a):", ["0 - <2kg", "1 - 2-10kg", "2 - >10kg"], "0=<2kg, 1=2-10kg, 2=>10kg"),
            ("force_load_b", "負荷力量-身體 (force_load_b):", ["0 - <2kg", "1 - 2-10kg", "2 - >10kg"], "0=<2kg, 1=2-10kg, 2=>10kg"),
        ]
        
        row = 0
        for param_key, param_name, options, param_desc in param_config:
            # 參數名稱
            name_label = QLabel(param_name)
            name_label.setStyleSheet("font-weight: bold; color: #ecf0f1;")
            grid_layout.addWidget(name_label, row, 0)
            
            # 下拉選單
            combo = QComboBox()
            combo.addItems(options)
            current_value = getattr(config.RULA_CONFIG, param_key, config.RULA_CONFIG[param_key])
            combo.setCurrentIndex(current_value)
            self.combos[param_key] = combo
            grid_layout.addWidget(combo, row, 1)
            row += 1
            
            # 參數說明
            desc_label = QLabel(param_desc)
            desc_label.setStyleSheet("font-size: 11px; color: #95a5a6; margin-bottom: 8px;")
            desc_label.setWordWrap(True)
            grid_layout.addWidget(desc_label, row, 0, 1, 2)
            row += 1
        
        layout.addLayout(grid_layout)
        layout.addStretch()
        
        # 按鈕佈局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 保存按鈕
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_config)
        button_layout.addWidget(save_button)
        
        # 關閉按鈕
        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_config(self):
        """Save the current parameter values back to config"""
        for param_key, combo in self.combos.items():
            # Extract the numeric value from the option string (e.g., "0 - <2kg" -> 0)
            value = int(combo.currentText().split(" ")[0])
            config.RULA_CONFIG[param_key] = value
        
        # Optionally show confirmation or just close
        self.accept()    