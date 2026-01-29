# File Structure Comparison

## BEFORE: God Class Pattern (mainwindow.py ~980 lines)

```
src/rula_realtime_app/ui/
├── main_window.py (980 lines) 🔴 MONOLITHIC
│   ├── __init__()
│   ├── init_ui() - UI construction + panel creation
│   ├── create_score_panel() - ❌ Not reusable
│   ├── start_detection()
│   ├── stop_detection()
│   ├── on_frame_ready()
│   ├── on_kinect_frame_ready()
│   ├── update_score_panel() - Panel logic mixed in
│   ├── update_coordinates_panel() - Panel logic mixed in
│   ├── display_frame() - Rendering logic mixed in
│   ├── on_error()
│   ├── on_fps_updated()
│   ├── toggle_pause()
│   ├── save_snapshot() - File I/O logic mixed in
│   ├── draw_scores_on_frame() - ❌ Not reusable
│   ├── get_panel_score() - ❌ Helper method
│   ├── save_scores_to_text() - File I/O
│   ├── write_panel_scores() - File I/O helper
│   ├── save_coordinates_to_text() - File I/O
│   ├── show_config_dialog() - Dialog logic mixed in
│   └── closeEvent()
├── components.py (incomplete)
├── dialogs.py (skeleton)
└── styles.py
```

**Issues**:
- ❌ 980 lines in single class
- ❌ Mixed concerns (UI, rendering, file I/O, dialogs)
- ❌ Low reusability
- ❌ Hard to test independently
- ❌ Difficult to maintain and extend

---

## AFTER: Component-Based Architecture (modular)

```
src/rula_realtime_app/ui/
├── main_window.py (520 lines) ✅ ORCHESTRATOR ONLY
│   ├── __init__()
│   ├── init_ui() - Creates components
│   ├── start_detection()
│   ├── stop_detection()
│   ├── on_frame_ready() - Coordinates components
│   ├── on_kinect_frame_ready() - Coordinates components
│   ├── update_score_panel() - Delegates to ScorePanel
│   ├── display_frame() - Delegates to FrameRenderer
│   ├── on_error()
│   ├── on_fps_updated()
│   ├── toggle_pause()
│   ├── save_snapshot() - Delegates to SnapshotManager
│   ├── show_config_dialog() - Uses RULAConfigDialog
│   └── closeEvent()
│
├── components.py ✅ REUSABLE COMPONENTS
│   ├── ScorePanel(QGroupBox)
│   │   ├── __init__()
│   │   ├── update_score_panel()
│   │   ├── reset_panel()
│   │   └── get_score()
│   │
│   ├── CoordinatesPanel(QGroupBox)
│   │   ├── __init__()
│   │   ├── update_coordinates()
│   │   ├── reset_panel()
│   │   └── get_text()
│   │
│   ├── FrameRenderer (static utility)
│   │   ├── display_frame()
│   │   └── draw_scores_on_frame()
│   │
│   └── SnapshotManager (static utility)
│       ├── save_rula_snapshot()
│       ├── save_coordinates_snapshot()
│       ├── ensure_directory_exists()
│       ├── _save_rula_scores_to_text()
│       ├── _save_coordinates_to_text()
│       └── _write_panel_scores()
│
├── dialogs.py ✅ DIALOG WINDOWS
│   └── RULAConfigDialog(QDialog)
│       ├── __init__()
│       └── [configuration display logic]
│
└── styles.py (unchanged)
```

**Benefits**:
- ✅ -46% code in MainWindow (980 → 520 lines)
- ✅ Clear separation of concerns
- ✅ Highly reusable components
- ✅ Independently testable classes
- ✅ Easy to extend and maintain
- ✅ Follows SOLID principles

---

## Dependency Flow

### BEFORE: Tight Coupling
```
MainWindow
├── Manages UI creation
├── Manages panel updates
├── Manages frame rendering
├── Manages file I/O
├── Manages dialogs
└── Manages detection flow
```
**Problem**: Everything depends on MainWindow

### AFTER: Clean Separation
```
MainWindow (Orchestration)
│
├── ScorePanel ────────→ Handles own updates & resets
├── CoordinatesPanel ──→ Handles own updates & resets
├── FrameRenderer ─────→ Static rendering utilities
├── SnapshotManager ───→ Static file I/O utilities
└── RULAConfigDialog ──→ Static configuration display
```
**Benefit**: Each component is independent and testable

---

## Size Metrics

| File | Before | After | Change |
|------|--------|-------|--------|
| main_window.py | 979 lines | 520 lines | -46.9% ✅ |
| components.py | 289 lines | 447 lines | +54.7% (added 158 lines of reusable code) |
| dialogs.py | 29 lines | 68 lines | +134.5% (complete implementation) |
| **Total** | 1,297 lines | 1,035 lines | -20.2% (more organized) |

---

## Reusability Score

### BEFORE
- ScorePanel: ❌ Cannot reuse (logic in MainWindow)
- FrameRenderer: ❌ Cannot reuse (logic in MainWindow)
- SnapshotManager: ❌ Cannot reuse (logic in MainWindow)
- ConfigDialog: ❌ Cannot reuse (logic in MainWindow)

### AFTER
- ScorePanel: ✅ Can import and use anywhere
- FrameRenderer: ✅ Can import and use anywhere
- SnapshotManager: ✅ Can import and use anywhere
- RULAConfigDialog: ✅ Can import and use anywhere

---

## Maintenance Simplification

### Code Organization
- **Before**: Find and update logic scattered across 980 lines
- **After**: Find logic in dedicated specialized classes

### Example: Update frame display
- **Before**: Modify `display_frame()` method in MainWindow (searching 980 lines)
- **After**: Modify `FrameRenderer.display_frame()` in components.py (isolated location)

### Example: Change snapshot format
- **Before**: Modify multiple methods (`save_scores_to_text()`, `draw_scores_on_frame()`, etc.)
- **After**: Modify `SnapshotManager._save_rula_scores_to_text()` in one place

---

## Testing Capability

### BEFORE
```python
# Hard to test - everything depends on MainWindow
def test_frame_display():
    window = MainWindow()  # Creates entire window
    # Test display_frame() method mixed with 1000 other lines
    # Hard to isolate and test
```

### AFTER
```python
# Easy to test - components are isolated
def test_frame_renderer():
    FrameRenderer.display_frame(mock_label, test_frame)
    # Simple, focused test

def test_snapshot_saving():
    success, msg = SnapshotManager.save_rula_snapshot(frame, left, right)
    # Can test without entire MainWindow
```
