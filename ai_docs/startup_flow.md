# RULA 即時評估系統 - 啟動流程分析

## 概覽
此文件追蹤 `main.py` 的完整啟動流程，包含所有模組的初始化順序與職責。

---

## 📌 啟動流程圖

```
main.py (執行入口)
  ↓
main() 函式
  ↓
QApplication (PyQt6 應用程式)
  ↓
MainWindow (主視窗)
  ↓
├─ config.py (載入配置)
├─ PoseDetector / KinectHandler (骨架辨識)
├─ CameraHandler (攝像頭) [當點擊「開始」時]
└─ RULA Calculator (角度與評分計算)
```

---

## 1️⃣ 主程式入口：`main.py`

### 檔案位置
[rula_realtime_app/main.py](rula_realtime_app/main.py)

### 執行流程
```python
def main():
    """主程式入口"""
    # 1. 創建 PyQt6 應用程式
    app = QApplication(sys.argv)
    
    # 2. 設定 UI 風格為 Fusion
    app.setStyle('Fusion')
    
    # 3. 創建並顯示主視窗
    window = MainWindow()
    window.show()
    
    # 4. 啟動事件循環
    sys.exit(app.exec())
```

### 職責
- 初始化 PyQt6 應用程式環境
- 創建主視窗實例並啟動 GUI 事件循環
- 設定路徑（支援從專案外部執行）

---

## 2️⃣ 主視窗初始化：`MainWindow`

### 檔案位置
[rula_realtime_app/ui/main_window.py](rula_realtime_app/ui/main_window.py)

### 初始化流程 (`__init__`)

#### Step 1: 載入配置模組
```python
from core.config import RULA_CONFIG, USE_KINECT
```
- 讀取 `config.py`，決定使用 **Azure Kinect** 或 **攝像頭 + MediaPipe**
- 載入 RULA 計算參數（手腕扭轉、腿部姿勢、肌肉使用等）

#### Step 2: 條件性匯入硬體模組
```python
if USE_KINECT:
    from core.kinect_handler import KinectHandler
    KINECT_AVAILABLE = True
else:
    KINECT_AVAILABLE = False
```

#### Step 3: 初始化核心元件
```python
# 攝像頭/Kinect 處理器（啟動時為 None，點擊「開始」後才創建）
self.camera_handler = None
self.kinect_handler = None

# 骨架辨識器（僅 MediaPipe 模式需要預先初始化）
self.pose_detector = None if USE_KINECT else PoseDetector()

# RULA 計算用的狀態變數
self.prev_left = None      # 前一幀左側分數（用於低置信度處理）
self.prev_right = None     # 前一幀右側分數
self.current_frame = None  # 當前影像幀

# 效能控制
self.frame_counter = 0
self.rula_calc_every_n_frames = 5  # 每5幀才計算一次 RULA
```

#### Step 4: 初始化 UI
```python
self.init_ui()
```
- 建立視窗佈局（影像顯示區、控制按鈕、分數面板）
- 創建左右側 RULA 評估面板

---

## 3️⃣ 配置模組：`config.py`

### 檔案位置
[rula_realtime_app/core/config.py](rula_realtime_app/core/config.py)

### 職責
集中管理所有配置參數，包括：

#### 硬體選擇
```python
USE_KINECT = True  # True: Azure Kinect; False: MediaPipe
```

#### Azure Kinect 配置
```python
KINECT_SDK_PATH = r"C:\Program Files\Azure Kinect SDK v1.4.1\..."
KINECT_BODY_TRACKING_PATH = r"C:\Program Files\Azure Kinect Body Tracking SDK\..."
KINECT_RESOLUTION = "1080P"
KINECT_DEPTH_MODE = "WFOV_2x2BINNED"
```

#### RULA 計算參數
```python
RULA_CONFIG = {
    'wrist_twist': 1,      # 手腕扭轉
    'legs': 1,             # 腿部姿勢
    'muscle_use_a': 0,     # Table A 肌肉使用
    'muscle_use_b': 0,     # Table B 肌肉使用
    'force_load_a': 0,     # Table A 負荷力量
    'force_load_b': 0,     # Table B 負荷力量
}
```

#### MediaPipe 設定
```python
MEDIAPIPE_CONFIG = {
    'model_complexity': 0,              # 輕量模型
    'min_detection_confidence': 0.5,
    'min_tracking_confidence': 0.5,
    ...
}
```

#### 其他配置
- 採樣設定（影格採樣間隔、存檔格式）
- 關節映射表（Azure Kinect ↔ MediaPipe）

---

## 4️⃣ 骨架辨識模組

### 4A. MediaPipe 模式：`PoseDetector`

#### 檔案位置
[rula_realtime_app/core/pose_detector.py](rula_realtime_app/core/pose_detector.py)

#### 初始化 (`__init__`)
```python
def __init__(self):
    # 匯入 MediaPipe 模組
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    
    # 創建 Pose 物件（根據 MEDIAPIPE_CONFIG 設定參數）
    self.pose = mp_pose.Pose(
        model_complexity=0,
        min_detection_confidence=0.5,
        ...
    )
    
    self.results = None  # 儲存辨識結果
```

#### 職責
- **`process_frame(frame)`**: 辨識骨架關鍵點
- **`get_landmarks_array()`**: 輸出 33 個關鍵點的 [x, y, z, visibility] 陣列
- **`draw_landmarks(image)`**: 在影像上繪製骨架線條

---

### 4B. Azure Kinect 模式：`KinectHandler`

#### 檔案位置
[rula_realtime_app/core/kinect_handler.py](rula_realtime_app/core/kinect_handler.py)

#### 初始化 (`__init__`)
```python
def __init__(self):
    super().__init__()  # 繼承 QThread
    
    # 初始化 Kinect 裝置和 Body Tracker（在 run() 方法中執行）
    self.device = None
    self.body_tracker = None
    self.running = False
```

#### 職責
- **QThread 執行緒**：非阻塞讀取 Kinect 影像和骨架數據
- **`run()`**: 啟動 Kinect 裝置，持續讀取影像幀和骨架
- **`skeleton_to_pose_array(skeleton)`**: 將 Kinect 骨架轉換為 MediaPipe 格式（33 關鍵點）
- **信號發送**：
  - `frame_ready.emit(frame, pose)` - 發送影像和骨架數據
  - `fps_updated.emit(fps)` - 更新 FPS
  - `error_occurred.emit(msg)` - 錯誤訊息

---

## 5️⃣ 攝像頭處理模組：`CameraHandler`

### 檔案位置
[rula_realtime_app/core/camera_handler.py](rula_realtime_app/core/camera_handler.py)

### 初始化 (`__init__`)
```python
def __init__(self, camera_index=0):
    super().__init__()  # 繼承 QThread
    
    self.camera_index = camera_index
    self.cap = None      # OpenCV VideoCapture 物件
    self.running = False
```

### 職責
- **QThread 執行緒**：非阻塞讀取攝像頭影像
- **`run()`**: 
  - 開啟攝像頭（`cv2.VideoCapture`）
  - 設定解析度（480x360）和 FPS（30）
  - 持續讀取影像幀並水平翻轉（鏡像模式）
- **信號發送**：
  - `frame_ready.emit(frame)` - 發送 RGB 影像
  - `fps_updated.emit(fps)` - 更新 FPS

---

## 6️⃣ RULA 計算模組

### 6A. 角度計算：`rula_calculator.py`

#### 檔案位置
[rula_realtime_app/core/rula_calculator.py](rula_realtime_app/core/rula_calculator.py)

#### 主要函式

##### `angle_calc(pose, previous_left, previous_right)`
- **輸入**: 33 關鍵點陣列、前一幀左右側分數
- **輸出**: (rula_left, rula_right) 字典
- **流程**:
  ```python
  rula_left = rula_score_side(pose, 'Left', previous_left)
  rula_right = rula_score_side(pose, 'Right', previous_right)
  ```

##### `rula_score_side(pose, side, previous_scores)`
1. **提取關鍵點** - 取得肩、肘、腕、頸、軀幹、髖等關節位置
2. **計算向量與角度** - 使用 `safe_angle()` 計算各部位角度
3. **檢查置信度** - 使用 `check_confidence()` 驗證關鍵點可靠性
4. **計算部位分數** - 根據角度範圍映射到 RULA 分數（1-4 分）
5. **查表計算總分** - 呼叫 `rula_risk()` 使用 Table A/B/C 計算最終分數

##### `rula_risk(...)`
- 使用 RULA 標準查表（`rula_tables.py`）
- 計算 **Table A**（上肢）、**Table B**（頸/軀幹/腿）、**Table C**（合成分數）

---

### 6B. 工具函式：`utils.py`

#### 檔案位置
[rula_realtime_app/core/utils.py](rula_realtime_app/core/utils.py)

#### 主要函式
- **`safe_angle(u, v)`**: 計算兩向量夾角（避免數值誤差）
- **`safe_unit_vector(v)`**: 安全的向量單位化（避免零長度）
- **`check_confidence(landmarks, indices, min_conf)`**: 檢查關鍵點置信度
- **`get_best_rula_score(rula_left, rula_right)`**: 取左右較高分數

---

## 7️⃣ 使用者操作流程

### 點擊「開始」按鈕 → `start_detection()`

#### MediaPipe 模式
```python
def start_detection(self):
    # 1. 創建攝像頭處理器
    self.camera_handler = CameraHandler(camera_index=0)
    
    # 2. 連接信號與槽函式
    self.camera_handler.frame_ready.connect(self.on_frame_ready)
    self.camera_handler.error_occurred.connect(self.on_error)
    self.camera_handler.fps_updated.connect(self.on_fps_updated)
    
    # 3. 啟動執行緒
    self.camera_handler.start()
```

#### Azure Kinect 模式
```python
def start_detection(self):
    # 1. 創建 Kinect 處理器
    self.kinect_handler = KinectHandler()
    
    # 2. 連接信號與槽函式
    self.kinect_handler.frame_ready.connect(self.on_kinect_frame_ready)
    self.kinect_handler.error_occurred.connect(self.on_error)
    self.kinect_handler.fps_updated.connect(self.on_fps_updated)
    
    # 3. 啟動執行緒
    self.kinect_handler.start()
```

---

### 影像處理循環

#### MediaPipe 模式：`on_frame_ready(frame)`
```python
def on_frame_ready(self, frame):
    # 1. 每幀進行骨架辨識
    detected = self.pose_detector.process_frame(frame)
    
    if detected:
        # 2. 繪製骨架
        annotated = self.pose_detector.draw_landmarks(frame)
        
        # 3. 每 5 幀才計算 RULA（降低 CPU 負擔）
        if self.frame_counter % 5 == 0:
            landmarks = self.pose_detector.get_landmarks_array()
            rula_left, rula_right = angle_calc(landmarks, self.prev_left, self.prev_right)
            
            # 4. 儲存分數（供下次低置信度使用）
            self.prev_left = rula_left
            self.prev_right = rula_right
            
            # 5. 更新 UI 分數面板
            self.update_score_panel(self.left_group, rula_left)
            self.update_score_panel(self.right_group, rula_right)
    
    # 6. 顯示影像
    self.display_frame(annotated)
```

#### Azure Kinect 模式：`on_kinect_frame_ready(frame, pose)`
```python
def on_kinect_frame_ready(self, frame, pose):
    # 1. Kinect 已在影像上繪製骨架，直接使用
    annotated = frame
    
    # 2. 如果有骨架數據，進行 RULA 計算
    if pose is not None:
        if self.frame_counter % 5 == 0:
            rula_left, rula_right = angle_calc(pose, self.prev_left, self.prev_right)
            
            self.prev_left = rula_left
            self.prev_right = rula_right
            
            self.update_score_panel(self.left_group, rula_left)
            self.update_score_panel(self.right_group, rula_right)
    
    # 3. 顯示影像
    self.display_frame(annotated)
```

---

## 8️⃣ 完整資料流總結

### 啟動階段
```
main.py → QApplication → MainWindow.__init__()
  ↓
載入 config.py (USE_KINECT, RULA_CONFIG)
  ↓
條件性初始化 PoseDetector (僅 MediaPipe 模式)
```

### 執行階段（點擊「開始」）
```
start_detection() → 創建 CameraHandler/KinectHandler
  ↓
啟動 QThread 執行緒
  ↓
[攝像頭/Kinect] 持續讀取影像
  ↓
發送 frame_ready 信號
  ↓
on_frame_ready() / on_kinect_frame_ready()
  ↓
├─ 骨架辨識（MediaPipe 模式）
├─ 繪製骨架
├─ 每 5 幀計算 RULA (angle_calc → rula_score_side → rula_risk)
└─ 更新 UI 顯示
```

---

## 9️⃣ 模組依賴關係圖

```
main.py
  └─ ui/main_window.py
      ├─ core/config.py (配置)
      ├─ core/camera_handler.py (攝像頭執行緒)
      ├─ core/kinect_handler.py (Kinect 執行緒)
      ├─ core/pose_detector.py (MediaPipe 骨架辨識)
      ├─ core/rula_calculator.py (RULA 計算)
      │   ├─ core/rula_tables.py (查表數據)
      │   └─ core/utils.py (工具函式)
      └─ core/__init__.py (匯出介面)
```

---

## 🔟 關鍵設計決策

### 1. 雙模式支援
- 透過 `USE_KINECT` 開關切換硬體源
- 統一的骨架數據格式（33 關鍵點）

### 2. 執行緒分離
- 攝像頭/Kinect 讀取在獨立 QThread
- 避免阻塞 UI 主執行緒，保持介面流暢

### 3. 效能優化
- 降低 RULA 計算頻率（每 5 幀）
- MediaPipe 使用輕量模型（complexity=0）
- 攝像頭解析度降至 480x360

### 4. 低置信度處理
- 儲存前一幀分數 (`prev_left`, `prev_right`)
- 關鍵點置信度不足時，可選擇沿用前值

### 5. 模組化設計
- 配置集中在 `config.py`
- 計算邏輯與 UI 分離
- 清晰的信號-槽機制

---

## 📝 總結

此系統採用 **事件驅動架構**，透過 PyQt6 的信號-槽機制實現模組間的解耦。啟動流程清晰分為：
1. **應用程式初始化**（main.py → MainWindow）
2. **配置載入**（config.py）
3. **硬體啟動**（CameraHandler / KinectHandler）
4. **即時處理循環**（骨架辨識 → RULA 計算 → UI 更新）

所有計算密集型任務（攝像頭讀取、骨架辨識）皆在獨立執行緒執行，確保 UI 反應靈敏。
