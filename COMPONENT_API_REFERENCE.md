# Component API Reference

## Quick Start Guide

### ScorePanel - RULA Score Display Widget

```python
from rula_realtime_app.ui.components import ScorePanel

# Create a score panel
left_panel = ScorePanel("Left Side RULA Evaluation")

# Update with RULA calculation results
rula_result = {
    'upper_arm_angle': 45,
    'upper_arm_score': 2,
    'lower_arm_angle': 30,
    'lower_arm_score': 1,
    'wrist_angle': 15,
    'wrist_score': 1,
    'neck_angle': 20,
    'neck_score': 2,
    'trunk_angle': 40,
    'trunk_score': 3,
    'wrist_and_arm_score': 5,
    'neck_trunk_leg_score': 4,
    'score': 6,  # Final RULA score
}
left_panel.update_score_panel(rula_result)

# Get current score
current_score = left_panel.get_score()  # Returns "6" or "N/A"

# Reset panel to initial state
left_panel.reset_panel()
```

---

### CoordinatesPanel - Keypoint Coordinates Display

```python
from rula_realtime_app.ui.components import CoordinatesPanel

# Create coordinates panel
coords_panel = CoordinatesPanel("Keypoint Coordinates")

# Update with landmark data
landmarks = [
    [x0, y0, z0, vis0],  # Nose
    [x1, y1, z1, vis1],  # ...
    # ... 33 total landmarks from MediaPipe
]
coords_panel.update_coordinates(landmarks)

# Get current text
text = coords_panel.get_text()

# Reset to initial state
coords_panel.reset_panel()
```

---

### FrameRenderer - Frame Display & Rendering Utilities

```python
from rula_realtime_app.ui.components import FrameRenderer

# Display frame in QLabel
FrameRenderer.display_frame(self.video_label, rgb_frame)

# Draw scores on frame
frame_copy = frame.copy()
FrameRenderer.draw_scores_on_frame(
    frame_copy, 
    left_score="6",
    right_score="5"
)
# frame_copy is now modified with score overlay
```

---

### SnapshotManager - File Saving Utilities

```python
from rula_realtime_app.ui.components import SnapshotManager

# Ensure directory exists
SnapshotManager.ensure_directory_exists()

# Save RULA evaluation snapshot
success, message = SnapshotManager.save_rula_snapshot(
    frame=rgb_frame,
    left_panel=left_score_panel,
    right_panel=right_score_panel,
    parent_window=self
)
if success:
    print(message)  # "圖片: rula_snapshots/rula_20260129_120530.png..."
else:
    print(f"Error: {message}")

# Save coordinates snapshot
success, message = SnapshotManager.save_coordinates_snapshot(
    frame=rgb_frame,
    landmarks=landmark_list,
    parent_window=self
)
```

**Output Structure**:
```
rula_snapshots/
├── rula_20260129_120530.png      # Frame with score overlay
├── rula_20260129_120530.txt      # Score data
├── coordinates_20260129_120631.png
└── coordinates_20260129_120631.txt
```

---

### RULAConfigDialog - Configuration Display Dialog

```python
from rula_realtime_app.ui.dialogs import RULAConfigDialog

# Create and show dialog (read-only)
dialog = RULAConfigDialog(parent_window)
dialog.exec()

# Dialog displays:
# - wrist_twist: 1
#   (1=中立位置, 2=扭轉)
# - legs: 1
#   (1=平衡站立/坐姿, 2=不平衡)
# - muscle_use_a: 1
#   (0=無, 1=靜態/重複)
# - muscle_use_b: 1
#   (0=無, 1=靜態/重複)
# - force_load_a: 0
#   (0=<2kg, 1=2-10kg, 2=>10kg)
# - force_load_b: 0
#   (0=<2kg, 1=2-10kg, 2=>10kg)
```

---

## MainWindow Changes

### Before
```python
# Old way - everything in MainWindow
def on_frame_ready(self, frame):
    # ... 30 lines of logic ...
    self.display_frame(annotated)  # MainWindow method
    self.update_score_panel(self.left_group, rula_left)  # Complex logic
    # ...
```

### After
```python
# New way - delegated to components
def on_frame_ready(self, frame):
    # ... 20 lines of logic ...
    FrameRenderer.display_frame(self.video_label, annotated)  # Utility call
    self.left_group.update_score_panel(rula_left)  # Component method
    # ...
```

---

## Import Changes

### Old MainWindow imports
```python
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGroupBox, QGridLayout, 
                             QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from datetime import datetime
import os
import cv2
```

### New MainWindow imports
```python
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
import cv2

from .components import ScorePanel, CoordinatesPanel, FrameRenderer, SnapshotManager
from .dialogs import RULAConfigDialog
```

**Removed**: QGroupBox, QGridLayout, QDialog, QImage, QPixmap, datetime, os
**Added**: Component imports

---

## Common Usage Patterns

### Creating UI Layout
```python
# RULA mode
self.left_panel = ScorePanel("Left Side RULA Evaluation")
self.right_panel = ScorePanel("Right Side RULA Evaluation")
layout.addWidget(self.left_panel)
layout.addWidget(self.right_panel)

# Or Coordinates mode
self.coords_panel = CoordinatesPanel("Keypoint Coordinates")
layout.addWidget(self.coords_panel)
```

### Processing Frames
```python
def on_frame_ready(self, frame):
    # Render frame
    FrameRenderer.display_frame(self.video_label, frame)
    
    # Update panels based on mode
    if self.display_mode == "RULA":
        self.left_panel.update_score_panel(rula_left)
        self.right_panel.update_score_panel(rula_right)
    else:
        self.coords_panel.update_coordinates(landmarks)
```

### Saving Data
```python
def save_snapshot(self):
    if self.display_mode == "RULA":
        success, msg = SnapshotManager.save_rula_snapshot(
            self.current_frame, 
            self.left_panel, 
            self.right_panel
        )
    else:
        success, msg = SnapshotManager.save_coordinates_snapshot(
            self.current_frame, 
            landmarks
        )
    
    # Show message to user
    if success:
        QMessageBox.information(self, "Success", msg)
    else:
        QMessageBox.critical(self, "Error", msg)
```

### Resetting UI
```python
def stop_detection(self):
    if self.display_mode == "RULA":
        self.left_panel.reset_panel()
        self.right_panel.reset_panel()
    else:
        self.coords_panel.reset_panel()
```

### Showing Config Dialog
```python
def show_config_dialog(self):
    dialog = RULAConfigDialog(self)
    dialog.exec()
```

---

## Class Hierarchy

```
QGroupBox
├── ScorePanel
└── CoordinatesPanel

QDialog
└── RULAConfigDialog

FrameRenderer (no inheritance)
└── [Static utility methods only]

SnapshotManager (no inheritance)
└── [Static utility methods only]
```

---

## Method Cheat Sheet

| Component | Method | Parameters | Returns | Purpose |
|-----------|--------|-----------|---------|---------|
| ScorePanel | update_score_panel() | rula_data: dict | None | Update angle/score labels |
| ScorePanel | reset_panel() | None | None | Reset all to "--" |
| ScorePanel | get_score() | None | str | Get Table C score |
| CoordinatesPanel | update_coordinates() | landmarks: list | None | Update coordinate display |
| CoordinatesPanel | reset_panel() | None | None | Reset to "等待骨架數據..." |
| CoordinatesPanel | get_text() | None | str | Get coordinate text |
| FrameRenderer | display_frame() | label, frame | None | Render frame to QLabel |
| FrameRenderer | draw_scores_on_frame() | frame, left, right | None | Draw scores overlay |
| SnapshotManager | ensure_directory_exists() | None | None | Create snapshots dir |
| SnapshotManager | save_rula_snapshot() | frame, left, right | (bool, str) | Save RULA data |
| SnapshotManager | save_coordinates_snapshot() | frame, landmarks | (bool, str) | Save coordinates |
| RULAConfigDialog | exec() | None | int | Show dialog |

---

## Error Handling

### SnapshotManager Returns
```python
success, message = SnapshotManager.save_rula_snapshot(...)

# On success:
# (True, "圖片: path/to/file.png\n文本: path/to/file.txt")

# On error:
# (False, "Error message describing what went wrong")
```

### Recommended Usage
```python
success, message = SnapshotManager.save_rula_snapshot(...)
if success:
    QMessageBox.information(self, "Success", message)
else:
    QMessageBox.critical(self, "Error", message)
```

---

## File Output Locations

All snapshots saved in: `rula_snapshots/` (created automatically)

### RULA Mode Output
- Image: `rula_YYYYMMDD_HHMMSS.png` (with score overlay)
- Text: `rula_YYYYMMDD_HHMMSS.txt`

### Coordinates Mode Output
- Image: `coordinates_YYYYMMDD_HHMMSS.png`
- Text: `coordinates_YYYYMMDD_HHMMSS.txt`

### Text File Format (RULA)
```
RULA 即時評估結果
==================================================
時間: 2026-01-29 12:05:30

左側身體評估:
--------------------------------------------------
  上臂角度: 45° (分數: 2)
  前臂角度: 30° (分數: 1)
  手腕角度: 15° (分數: 1)
  頸部角度: 20° (分數: 2)
  軀幹角度: 40° (分數: 3)

  Table A 分數: 5
  Table B 分數: 4
  Table C 分數 (總分): 6

右側身體評估:
--------------------------------------------------
  上臂角度: 40° (分數: 2)
  前臂角度: 35° (分數: 1)
  手腕角度: 10° (分數: 1)
  頸部角度: 25° (分數: 2)
  軀幹角度: 35° (分數: 3)

  Table A 分數: 4
  Table B 分數: 5
  Table C 分數 (總分): 5
```

---

## Troubleshooting

### ScorePanel not updating
```python
# ✅ Correct: Call method on component
self.left_panel.update_score_panel(rula_data)

# ❌ Wrong: Old way won't work
self.update_score_panel(self.left_panel, rula_data)
```

### Frame not displaying
```python
# ✅ Correct: Use FrameRenderer
FrameRenderer.display_frame(self.video_label, frame)

# ❌ Wrong: Old method doesn't exist
self.display_frame(frame)
```

### Snapshot not saving
```python
# Always check return value
success, message = SnapshotManager.save_rula_snapshot(...)
if not success:
    print(f"Save failed: {message}")  # See what went wrong

# Common issues:
# - Frame is None
# - Panel objects are None or wrong type
# - Write permissions issue in rula_snapshots/ directory
```
