"""
RULA Realtime UI Styles - Macro-based stylesheet generation
Uses generator functions to reduce repetition and improve maintainability
"""

# ============================================================================
# COLOR PALETTE
# ============================================================================
# Dark theme colors
DARK_BG = "#2c3e50"
DARK_BG_ALT = "#34495e"
DARK_BG_RGBA = "rgba(44, 62, 80, 0.95)"
DARK_BG_ALT_RGBA = "rgba(52, 73, 94, 0.95)"
VERY_DARK = "#1a1a1a"

# Light colors
LIGHT_TEXT = "#ecf0f1"
LIGHT_GRAY = "#95a5a6"
DARK_GRAY = "#7f8c8d"
LIGHT_GRAY_INACTIVE = "#bdc3c7"

# Primary accent
PRIMARY_ACCENT = "#3498db"
DARK_ACCENT = "#34495e"

# Button colors
BTN_GREEN = "#27ae60"
BTN_GREEN_DARK = "#229954"
BTN_GREEN_LIGHT = "#2ecc71"
BTN_RED = "#e74c3c"
BTN_RED_DARK = "#c0392b"
BTN_RED_LIGHT = "#ec7063"
BTN_ORANGE = "#f39c12"
BTN_ORANGE_DARK = "#e67e22"
BTN_ORANGE_LIGHT = "#f4a742"
BTN_TEAL = "#16a085"
BTN_TEAL_DARK = "#138d75"
BTN_TEAL_LIGHT = "#1abc9c"
BTN_PURPLE = "#8e44ad"
BTN_PURPLE_DARK = "#6c3483"
BTN_PURPLE_LIGHT = "#9b59b6"

# ============================================================================
# STYLE GENERATORS (Macro functions)
# ============================================================================
def _button_style(normal_light, normal_dark, hover_light, hover_dark, 
                  pressed, width=100, height=None, font_size=16):
    """Generate button stylesheet with gradient, hover, and pressed states"""
    return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {normal_light}, stop:1 {normal_dark});
                color: white;
                font-size: {font_size}px;
                font-weight: bold;
                padding: {12 if font_size == 16 else 8}px {24 if font_size == 16 else 16}px;
                border: none;
                border-radius: 8px;
                min-width: {width}px;
                {f'max-width: {width}px;' if font_size > 16 else ''}
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {hover_light}, stop:1 {hover_dark});
            }}
            QPushButton:pressed {{
                background: {pressed};
            }}
            QPushButton:disabled {{
                background: {DARK_GRAY};
                color: {LIGHT_GRAY_INACTIVE};
            }}
        """

def _group_box_style(title_content=""):
    """Generate group box stylesheet for panels"""
    return f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: bold;
                color: {PRIMARY_ACCENT};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {DARK_BG_RGBA}, stop:1 {DARK_BG_ALT_RGBA});
                border: 2px solid {PRIMARY_ACCENT};
                border-radius: 12px;
                margin-top: 15px;
                padding: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 15px;
                background-color: {DARK_BG};
                border-radius: 6px;
            }}
            {title_content}
        """

def _messagebox_style(font_size=11, label_min_width=""):
    """Generate message box stylesheet (QMessageBox and dialogs)"""
    min_width = f"min-width: {label_min_width};" if label_min_width else ""
    return f"""
            QMessageBox {{
                background-color: white;
            }}
            QLabel {{
                color: black;
                font-size: {font_size}px;
                {min_width}
            }}
            QPushButton {{
                color: black;
                background-color: #e0e0e0;
                border: 1px solid #999;
                padding: 5px 15px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: #d0d0d0;
            }}
        """

def _dialog_style():
    """Generate dialog stylesheet with dark theme and combo boxes"""
    return f"""
            QDialog {{
                background-color: {DARK_BG};
                color: {LIGHT_TEXT};
            }}
            QLabel {{
                color: {LIGHT_TEXT};
                font-size: 13px;
            }}
            QComboBox {{
                background-color: {DARK_BG_ALT};
                color: {LIGHT_TEXT};
                border: 1px solid {PRIMARY_ACCENT};
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
                min-width: 100px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_BG_ALT};
                color: {LIGHT_TEXT};
                selection-background-color: {PRIMARY_ACCENT};
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {PRIMARY_ACCENT}, stop:1 #2980b9);
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 {PRIMARY_ACCENT});
            }}
        """

# ============================================================================
# GENERATED STYLES
# ============================================================================
MAIN_WINDOW_STYLE = f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {DARK_BG}, stop:1 {DARK_BG_ALT});
            }}
            QWidget {{
                color: {LIGHT_TEXT};
                font-family: "Microsoft JhengHei", "微軟正黑體", Arial;
            }}
            QLabel {{
                color: {LIGHT_TEXT};
            }}
        """

# Button styles using macro
START_BUTTON_STYLE = _button_style(BTN_GREEN_LIGHT, BTN_GREEN, BTN_GREEN_LIGHT, BTN_GREEN, BTN_GREEN_DARK)
STOP_BUTTON_STYLE = _button_style(BTN_RED, BTN_RED_DARK, BTN_RED_LIGHT, BTN_RED, BTN_RED_DARK)
PAUSE_BUTTON_STYLE = _button_style(BTN_ORANGE, BTN_ORANGE_DARK, BTN_ORANGE_LIGHT, BTN_ORANGE, BTN_ORANGE_DARK)
SAVE_BUTTON_STYLE = _button_style(BTN_TEAL, BTN_TEAL_DARK, BTN_TEAL_LIGHT, BTN_TEAL, BTN_TEAL_DARK)
CONFIG_BUTTON_STYLE = _button_style(BTN_PURPLE, BTN_PURPLE_DARK, BTN_PURPLE_LIGHT, BTN_PURPLE, BTN_PURPLE_DARK, 
                                     width=50, font_size=24)

# Message box styles using macro
ERROR_MESSAGEBOX_STYLE = _messagebox_style(font_size=11)
SUCCESS_MESSAGEBOX_STYLE = _messagebox_style(font_size=11)
MESSAGEBOX_WIDE_STYLE = _messagebox_style(font_size=12, label_min_width="200px")

# Dialog style using macro
RULA_CONFIG_DIALOG_STYLE = _dialog_style()

VIDEO_LABEL_STYLE = f"""
            border: 3px solid {PRIMARY_ACCENT};
            border-radius: 10px;
            background-color: {VERY_DARK};
            font-size: 16px;
            color: {LIGHT_GRAY};
        """

# Panel styles using macro
_PANEL_LABEL = f"""
            QLabel {{
                color: {LIGHT_TEXT};
                background: transparent;
            }}
        """

_PANEL_TEXTEDIT = f"""
            QTextEdit {{
                background-color: rgba(26, 26, 26, 0.8);
                color: {LIGHT_TEXT};
                border: 1px solid {DARK_ACCENT};
                border-radius: 5px;
                font-family: "Courier New", monospace;
                font-size: 11px;
                padding: 5px;
            }}
        """

SCORE_PANEL_STYLE = _group_box_style(_PANEL_LABEL)
COORDINATES_PANEL_STYLE = _group_box_style(_PANEL_LABEL + _PANEL_TEXTEDIT)

FPS_LABEL_STYLE = f"""
            font-size: 16px;
            font-weight: bold;
            padding: 12px 20px;
            background-color: rgba(52, 73, 94, 0.7);
            border-radius: 8px;
            color: {PRIMARY_ACCENT};
        """

# Record button style (Red when recording)
RECORD_BUTTON_STYLE = _button_style(
    normal_light=BTN_RED_LIGHT,
    normal_dark=BTN_RED_DARK,
    hover_light=BTN_RED_LIGHT,
    hover_dark=BTN_RED,
    pressed=BTN_RED_DARK,
    width=100,
    font_size=16
)

# Record button style (Inactive/Ready to record)
RECORD_BUTTON_READY_STYLE = _button_style(
    normal_light="#7f8c8d",
    normal_dark="#5d6d7e",
    hover_light="#95a5a6",
    hover_dark="#7f8c8d",
    pressed="#5d6d7e",
    width=100,
    font_size=16
)