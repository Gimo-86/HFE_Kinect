"""
RULA 即時評估系統 - 主程式
"""

import sys
import os
import argparse

# 將當前目錄加入 Python 路徑（支援從外部執行）
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from .ui.main_window import MainWindow
from .core import config


def main():
    """主程式入口"""
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='RULA 即時評估系統')
    parser.add_argument(
        '-d',
        '--display-mode',
        type=str,
        choices=['RULA', 'COORDINATES'],
        default=config.DISPLAY_MODE,
        help='顯示模式: RULA (顯示RULA評估分數) 或 COORDINATES (顯示關鍵點坐標)'
    )
    parser.add_argument(
        '-c',
        '--camera-mode',
        type=str,
        choices=['WEBCAM', 'KINECT', 'KINECT_RGB'],
        default=config.CAMERA_MODE,
        help='相機模式: WEBCAM, KINECT, 或 KINECT_RGB'
    )
    args = parser.parse_args()
    
    # 更新配置
    config.DISPLAY_MODE = args.display_mode
    config.CAMERA_MODE = args.camera_mode
    
    print(f"啟動設定: 顯示模式={config.DISPLAY_MODE}, 相機模式={config.CAMERA_MODE}")
    
    # 創建應用程式
    app = QApplication(sys.argv)
    
    # 設定應用程式樣式
    app.setStyle('Fusion')
    
    # 創建主視窗
    window = MainWindow()
    window.show()
    
    # 執行應用程式
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
