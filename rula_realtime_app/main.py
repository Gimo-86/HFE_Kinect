"""
RULA 即時評估系統 - 主程式
"""

import sys
import os

# 將當前目錄加入 Python 路徑（支援從外部執行）
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """主程式入口"""
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
