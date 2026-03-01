"""
Dialog windows for RULA application
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QGridLayout, QPushButton)
from ..core import config
from .styles import RULA_CONFIG_DIALOG_STYLE
from .language import language_manager, t


class RULAConfigDialog(QDialog):
    """Configuration dialog for RULA parameters with dropdown controls"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = language_manager
        self.lang.add_observer(self.on_language_changed)
        
        self.setWindowTitle(t('config_title'))
        self.setMinimumSize(500, 450)
        self.setStyleSheet(RULA_CONFIG_DIALOG_STYLE)
        
        # Store references to combo boxes for retrieval
        self.combos = {}
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        self.title_label = QLabel(t('config_subtitle'))
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        # 參數網格
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setColumnStretch(0, 2)
        grid_layout.setColumnStretch(1, 1)
        
        # 保存標籤引用以便語言切換時更新
        self.param_name_labels = {}
        self.param_desc_labels = {}
        
        # Define parameter options with translation keys
        param_config = [
            ("wrist_twist", "config_wrist_twist", "config_wrist_twist_desc", 
             ["config_option_wrist_1", "config_option_wrist_2"]),
            ("legs", "config_legs", "config_legs_desc",
             ["config_option_legs_1", "config_option_legs_2"]),
            ("muscle_use_a", "config_muscle_use_a", "config_muscle_use_a_desc",
             ["config_option_muscle_0", "config_option_muscle_1"]),
            ("muscle_use_b", "config_muscle_use_b", "config_muscle_use_b_desc",
             ["config_option_muscle_0", "config_option_muscle_1"]),
            ("force_load_a", "config_force_load_a", "config_force_load_a_desc",
             ["config_option_force_0", "config_option_force_1", "config_option_force_2"]),
            ("force_load_b", "config_force_load_b", "config_force_load_b_desc",
             ["config_option_force_0", "config_option_force_1", "config_option_force_2"]),
        ]
        
        row = 0
        for param_key, name_key, desc_key, option_keys in param_config:
            # 參數名稱
            name_label = QLabel(t(name_key))
            name_label.setStyleSheet("font-weight: bold; color: #ecf0f1;")
            grid_layout.addWidget(name_label, row, 0)
            self.param_name_labels[param_key] = (name_label, name_key)
            
            # 下拉選單
            combo = QComboBox()
            # 添加翻譯的選項文本
            for opt_key in option_keys:
                combo.addItem(t(opt_key))
            current_value = getattr(config.RULA_CONFIG, param_key, config.RULA_CONFIG[param_key])
            combo.setCurrentIndex(current_value)
            self.combos[param_key] = (combo, option_keys)  # 保存combo和翻譯鍵
            grid_layout.addWidget(combo, row, 1)
            row += 1
            
            # 參數說明
            desc_label = QLabel(t(desc_key))
            desc_label.setStyleSheet("font-size: 11px; color: #95a5a6; margin-bottom: 8px;")
            desc_label.setWordWrap(True)
            grid_layout.addWidget(desc_label, row, 0, 1, 2)
            self.param_desc_labels[param_key] = (desc_label, desc_key)
            row += 1
        
        layout.addLayout(grid_layout)
        layout.addStretch()
        
        # 按鈕佈局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 保存按鈕
        self.save_button = QPushButton(t('config_save'))
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        
        # 關閉按鈕
        self.close_button = QPushButton(t('config_cancel'))
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_language_changed(self, lang_code):
        """語言改變時更新對話框文本"""
        self.setWindowTitle(t('config_title'))
        self.title_label.setText(t('config_subtitle'))
        self.save_button.setText(t('config_save'))
        self.close_button.setText(t('config_cancel'))
        
        # 更新參數名稱標籤
        for param_key, (label, name_key) in self.param_name_labels.items():
            label.setText(t(name_key))
        
        # 更新參數描述標籤
        for param_key, (label, desc_key) in self.param_desc_labels.items():
            label.setText(t(desc_key))
        
        # 更新下拉選單選項
        for param_key, (combo, option_keys) in self.combos.items():
            current_index = combo.currentIndex()
            combo.clear()
            for opt_key in option_keys:
                combo.addItem(t(opt_key))
            combo.setCurrentIndex(current_index)
    
    def save_config(self):
        """Save the current parameter values back to config"""
        for param_key, (combo, option_keys) in self.combos.items():
            # 直接使用選中的索引作為值
            value = combo.currentIndex()
            config.RULA_CONFIG[param_key] = value
        
        # Optionally show confirmation or just close
        self.accept()    