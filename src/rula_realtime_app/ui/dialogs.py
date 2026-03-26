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
        self.setWindowTitle(config.t("dialog_title"))
        self.setMinimumSize(500, 450)
        self.setStyleSheet(RULA_CONFIG_DIALOG_STYLE)
        
        # Store references to combo boxes for retrieval
        self.combos = {}
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        title_label = QLabel(config.t("dialog_heading"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 語言選擇
        language_layout = QHBoxLayout()
        language_label = QLabel(config.t("language_label"))
        language_label.setStyleSheet("font-weight: bold; color: #ecf0f1;")
        self.language_combo = QComboBox()

        language_codes = list(config.SUPPORTED_LANGUAGES.keys())
        for code in language_codes:
            self.language_combo.addItem(config.SUPPORTED_LANGUAGES[code], code)

        current_language_index = self.language_combo.findData(config.APP_LANGUAGE)
        if current_language_index >= 0:
            self.language_combo.setCurrentIndex(current_language_index)

        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        layout.addLayout(language_layout)
        
        # 參數網格
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setColumnStretch(0, 2)
        grid_layout.setColumnStretch(1, 1)
        
        # Define parameter options using localized text keys
        param_config = [
            (
                "wrist_twist",
                config.t("param_wrist_twist"),
                [config.t("option_1_neutral"), config.t("option_2_twist")],
                config.t("param_desc_wrist_twist"),
            ),
            (
                "legs",
                config.t("param_legs"),
                [config.t("option_1_balanced"), config.t("option_2_unbalanced")],
                config.t("param_desc_legs"),
            ),
            (
                "muscle_use_a",
                config.t("param_muscle_use_a"),
                [config.t("option_0_none"), config.t("option_1_static_repeat")],
                config.t("param_desc_muscle_use"),
            ),
            (
                "muscle_use_b",
                config.t("param_muscle_use_b"),
                [config.t("option_0_none"), config.t("option_1_static_repeat")],
                config.t("param_desc_muscle_use"),
            ),
            (
                "force_load_a",
                config.t("param_force_load_a"),
                [config.t("option_0_lt_2kg"), config.t("option_1_2_to_10kg"), config.t("option_2_gt_10kg")],
                config.t("param_desc_force_load"),
            ),
            (
                "force_load_b",
                config.t("param_force_load_b"),
                [config.t("option_0_lt_2kg"), config.t("option_1_2_to_10kg"), config.t("option_2_gt_10kg")],
                config.t("param_desc_force_load"),
            ),
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
            # Get current value from config dictionary
            current_value = config.RULA_CONFIG[param_key]
            # Find the index matching the current value (extract from "0 - <2kg" format)
            current_index = next((i for i, opt in enumerate(options) if int(opt.split(" ")[0]) == current_value), 0)
            combo.setCurrentIndex(current_index)
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
        save_button = QPushButton(config.t("save_button"))
        save_button.clicked.connect(self.save_config)
        button_layout.addWidget(save_button)
        
        # 關閉按鈕
        close_button = QPushButton(config.t("close_button"))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_config(self):
        """Save the current parameter values back to config"""
        selected_language = self.language_combo.currentData()
        if selected_language in config.SUPPORTED_LANGUAGES:
            config.APP_LANGUAGE = selected_language

        for param_key, combo in self.combos.items():
            # Extract the numeric value from the option string (e.g., "0 - <2kg" -> 0)
            value = int(combo.currentText().split(" ")[0])
            config.RULA_CONFIG[param_key] = value

        # 讓主視窗即時套用新語言
        parent = self.parent()
        if parent and hasattr(parent, "apply_language"):
            parent.apply_language()
        
        # Optionally show confirmation or just close
        self.accept()    