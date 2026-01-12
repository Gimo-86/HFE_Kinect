# PyQt6 即時RULA評估系統開發計劃

## 專案目標
建立一個基於PyQt6的即時骨架辨識與RULA評估系統，透過前置鏡頭與MediaPipe進行即時分析。

---

## 一、系統架構設計

### 1.1 專案結構（複製現有程式碼到 core/）
```
HFE_Kinect/
├── rula_realtime_app/               # 📁 新建應用程式資料夾
│   ├── main.py                      # 主程式入口（新建）
│   ├── __init__.py                  
│   │
│   ├── ui/                          # UI 元件
│   │   ├── __init__.py
│   │   ├── main_window.py           # 主視窗類別（新建）
│   │   ├── video_widget.py          # 影像顯示元件（新建）
│   │   └── score_panel.py           # 分數顯示面板（新建）
│   │
│   └── core/                        # 核心功能（所有核心邏輯）
│       ├── __init__.py
│       ├── camera_handler.py        # 攝像頭處理（新建）
│       ├── pose_detector.py         # MediaPipe骨架辨識（新建）
│       ├── rula_calculator.py       # ✅ 複製：RULA計算核心
│       ├── rula_tables.py           # ✅ 複製：評估表格
│       ├── utils.py                 # ✅ 複製：工具函數
│       └── video_config.py          # ✅ 複製：配置參數
│
├── rula_calculator.py               # 原始檔案
├── rula_tables.py                   # 原始檔案
├── utils.py                         # 原始檔案
├── video_config.py                  # 原始檔案
└── requirements.txt
```

### 1.2 檔案複製清單
需要從根目錄複製到 `rula_realtime_app/core/` 的檔案：
- ✅ `rula_calculator.py` → `rula_realtime_app/core/rula_calculator.py`
- ✅ `rula_tables.py` → `rula_realtime_app/core/rula_tables.py`
- ✅ `utils.py` → `rula_realtime_app/core/utils.py`
- ✅ `video_config.py` → `rula_realtime_app/core/video_config.py`

### 1.3 匯入方式（保持相對匯入）
**優點**：複製後的程式碼不需要修改，相對匯入可以正常運作
```python
# rula_realtime_app/core/rula_calculator.py 中
from .rula_tables import TABLE_A_DATA  # ✅ 保持不變
from .utils import safe_angle           # ✅ 保持不變
from .video_config import RULA_CONFIG   # ✅ 保持不變
```

**在新程式中匯入**：
```python
# rula_realtime_app/ui/main_window.py 中
from ..core.rula_calculator import angle_calc
from ..core.utils import get_best_rula_score
```

**在 core/__init__.py 中匯出主要函數**：
```python
# rula_realtime_app/core/__init__.py
from .rula_calculator import angle_calc, rula_score_side
from .utils import get_best_rula_score, safe_angle, check_confidence
from .video_config import MEDIAPIPE_CONFIG, RULA_CONFIG

__all__ = ['angle_calc', 'rula_score_side', 'get_best_rula_score', 
           'safe_angle', 'check_confidence', 'MEDIAPIPE_CONFIG', 'RULA_CONFIG']
```

---

## 二、UI介面設計

### 2.1 主視窗佈局
```
┌─────────────────────────────────────────────────────────┐
│  RULA 即時評估系統                          [最小化][關閉]│
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────┐  ┌────────────────────────┐│
│  │                         │  │  左側 RULA 評估         ││
│  │                         │  ├────────────────────────┤│
│  │   即時影像顯示區域        │  │  上臂角度: 25.3°       ││
│  │   (含骨架繪製)           │  │  前臂角度: 85.7°       ││
│  │   640x480               │  │  手腕角度: 12.4°       ││
│  │                         │  │  頸部角度: 15.2°       ││
│  │                         │  │  軀幹角度: 8.5°        ││
│  │                         │  ├────────────────────────┤│
│  │                         │  │  Table A 分數: 3       ││
│  │                         │  │  Table B 分數: 2       ││
│  │                         │  │  Table C 分數: 3       ││
│  │                         │  │  風險等級: Low risk    ││
│  └─────────────────────────┘  ├────────────────────────┤│
│                                │  右側 RULA 評估         ││
│  [開始] [停止] [設定]          │  (同上格式)            ││
│  FPS: 30                       │                        ││
└─────────────────────────────────────────────────────────┘
```

### 2.2 顯示元素
1. **影像區域**（左側）
   - 即時攝像頭畫面
   - MediaPipe骨架點繪製
   - 關鍵角度標註線

2. **評估面板**（右側）
   - 左側身體評估數據
   - 右側身體評估數據
   - 各部位角度數值
   - RULA分數（Table A、B、C）
   - 風險等級（顏色標示）

3. **控制區域**（底部）
   - 開始/停止按鈕
   - 設定按鈕（調整參數）
   - FPS顯示

---

## 三、技術實作細節

### 3.1 攝像頭處理 (camera_handler.py)
```python
class CameraHandler(QThread):
    """
    功能：
    - 使用 cv2.VideoCapture 取得前置鏡頭
    - 以 QThread 實現非阻塞讀取
    - 發送 frame_ready 信號傳遞影像
    
    主要方法：
    - start_camera(): 啟動攝像頭
    - stop_camera(): 停止攝像頭
    - run(): 執行緒主循環
    """
```

### 3.2 骨架辨識 (pose_detector.py)
```python
class PoseDetector:
    """
    功能：
    - 整合 MediaPipe Pose
    - 處理影像並偵測骨架
    - 回傳33個關鍵點座標與置信度
    
    主要方法：
    - __init__(): 初始化 MediaPipe
    - process_frame(frame): 處理單一幀
    - get_landmarks(): 取得關鍵點列表
    """
```

### 3.3 使用 core/ 內的 RULA 計算模組
**從 core 匯入**：
```python
# 方式1: 從 core 直接匯入（在 ui/main_window.py 中）
from ..core.rula_calculator import angle_calc
from ..core.utils import get_best_rula_score

# 方式2: 使用 core.__init__.py 匯出（推薦）
from ..core import angle_calc, get_best_rula_score

# 使用方式
pose_landmarks = convert_mediapipe_to_array(results.pose_landmarks)
rula_left, rula_right = angle_calc(pose_landmarks, prev_left, prev_right)
final_result = get_best_rula_score(rula_left, rula_right)
```

**座標轉換函數**（在 main_window.py 中實作）：
```python
def convert_mediapipe_to_array(landmarks):
    """將 MediaPipe landmarks 轉換為 rula_calculator 需要的格式"""
    pose = []
    for lm in landmarks.landmark:
        pose.append([lm.x, lm.y, lm.z, lm.visibility])
    return pose
```

### 3.4 主視窗 (main_window.py)
```python
class MainWindow(QMainWindow):
    """
    功能：
    - 整合所有UI元件
    - 協調攝像頭、辨識、計算流程
    - 更新顯示數據
    
    主要方法：
    - init_ui(): 初始化界面
    - start_detection(): 開始辨識
    - stop_detection(): 停止辨識
    - update_frame(): 更新影像與分數
    """
```

---

## 四、實作步驟

### 階段一：複製檔案與建立結構
1. ✅ 建立專案結構與規劃文件
2. ⬜ 建立 `rula_realtime_app/` 資料夾結構
3. ⬜ **複製檔案**到 `rula_realtime_app/core/`:
   - `rula_calculator.py`
   - `rula_tables.py`
   - `utils.py`
   - `video_config.py`
4. ⬜ 創建 `__init__.py` 檔案（含 core 匯出設定）
5. ⬜ 安裝依賴套件（PyQt6, mediapipe, opencv-python）

### 階段二：基礎UI與攝像頭
1. ⬜ 創建 `core/camera_handler.py` - 攝像頭執行緒
2. ⬜ 創建 `ui/main_window.py` - 基本視窗框架
3. ⬜ 測試攝像頭影像顯示
4. ⬜ 創建 `main.py` 啟動程式

### 階段三：骨架辨識整合
1. ⬜ 創建 `core/pose_detector.py` - MediaPipe整合
2. ⬜ 實作座標轉換函數
3. ⬜ 在影像上繪製骨架點與連線
4. ⬜ 測試骨架辨識效果

### 階段四：RULA計算整合
1. ⬜ 在主視窗中整合 `rula_calculator.angle_calc()`
2. ⬜ 處理前一幀資料維護
3. ⬜ 測試RULA分數計算準確性

### 階段五：分數顯示面板
1. ⬜ 創建 `ui/score_panel.py` - 分數顯示元件
2. ⬜ 實作左右側數據顯示
3. ⬜ 加入風險等級顏色標示
4. ⬜ 優化UI佈局與樣式


---

## 五、技術要點

### 5.1 座標系統轉換
```python
# MediaPipe 輸出格式
landmark = {
    'x': 0.5,      # 正規化座標 [0, 1]
    'y': 0.3,
    'z': -0.1,     # 深度資訊
    'visibility': 0.95
}

# 轉換為 RULA 計算格式
pose[i] = [x, y, z, visibility]  # NumPy array
```

### 5.2 執行緒安全
- 使用 `QThread` 處理攝像頭讀取
- 使用 `pyqtSignal` 進行執行緒間通訊
- 避免主執行緒阻塞

### 5.3 效能優化
- 控制處理幀率（建議15-30 FPS）
- 使用 MediaPipe 的 `static_image_mode=False`
- 必要時降低影像解析度

---

## 六、依賴套件

```txt
PyQt6>=6.6.0
mediapipe>=0.10.0
opencv-python>=4.8.0
numpy>=1.24.0
```

---

## 七、預期成果

### 基本功能
- ✅ 即時攝像頭畫面顯示
- ✅ MediaPipe 骨架辨識與繪製
- ✅ 左右側RULA分數即時計算
- ✅ 各部位角度顯示
- ✅ Table A、B、C分數顯示
- ✅ 風險等級顯示

### 進階功能（可選）
- ⬜ 分數歷史紀錄圖表
- ⬜ 截圖與報告輸出
- ⬜ 參數調整介面
- ⬜ 多人辨識支援

---

## 八、開發注意事項

### 8.1 檔案放入 core/ 的優勢
- **邏輯清晰**：所有核心功能（攝像頭、辨識、計算）集中在 core/
- **模組化設計**：UI 與核心邏輯完全分離
- **易於維護**：相關檔案集中管理
- **無需修改原始碼**：相對匯入（`.`）保持不變
- **獨立部署**：`rula_realtime_app/` 可獨立運作

### 8.2 錯誤處理
- 攝像頭無法開啟時的提示
- MediaPipe 初始化失敗處理
- 低置信度骨架點的處理策略

### 8.3 使用者體驗
- 清晰的狀態提示
- 流暢的畫面更新（>= 15 FPS）
- 直觀的風險等級顏色（綠/黃/橙/紅）

---

## 九、下一步行動

### 立即執行清單

#### 1. 建立資料夾結構
```bash
mkdir rula_realtime_app
mkdir rula_realtime_app\ui
mkdir rula_realtime_app\core
```

#### 2. 複製現有檔案到 core/
```bash
copy rula_calculator.py rula_realtime_app\core\
copy rula_tables.py rula_realtime_app\core\
copy utils.py rula_realtime_app\core\
copy video_config.py rula_realtime_app\core\
```

#### 3. 創建 __init__.py 檔案
```bash
type nul > rula_realtime_app\__init__.py
type nul > rula_realtime_app\ui\__init__.py
```

創建 `rula_realtime_app\core\__init__.py` 並加入匯出：
```python
# rula_realtime_app/core/__init__.py
from .rula_calculator import angle_calc, rula_score_side
from .utils import get_best_rula_score, safe_angle, check_confidence
from .video_config import MEDIAPIPE_CONFIG, RULA_CONFIG

__all__ = ['angle_calc', 'rula_score_side', 'get_best_rula_score', 
           'safe_angle', 'check_confidence', 'MEDIAPIPE_CONFIG', 'RULA_CONFIG']
```

#### 4. 創建核心程式檔案
按順序創建：
- ✅ `rula_realtime_app/core/camera_handler.py` - 攝像頭執行緒
- ✅ `rula_realtime_app/core/pose_detector.py` - MediaPipe封裝
- ✅ `rula_realtime_app/ui/main_window.py` - 主視窗
- ✅ `rula_realtime_app/ui/score_panel.py` - 分數面板
- ✅ `rula_realtime_app/main.py` - 程式入口

#### 5. 安裝依賴套件
```bash
pip install PyQt6 mediapipe opencv-python numpy
```

---

**備註**：
- ✅ 優點：不需修改原始程式碼
- ✅ 保持相對匯入結構不變
- ✅ 應用程式可獨立運作和部署
- ✅ 專案結構清晰易維護
