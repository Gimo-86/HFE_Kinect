import cv2
import os
import sys
from pathlib import Path
import numpy as np
import pykinect_azure as pykinect

# 確保可以導入 rula_realtime_app
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from rula_realtime_app.core.rula_calculator import angle_calc
from rula_realtime_app.core.utils import get_best_rula_score

# 1. 確保 DLL 路徑正確 (請確認這兩個路徑與您電腦中的實際路徑相符)
SDK_BIN = r"C:\Program Files\Azure Kinect SDK v1.4.1\sdk\windows-desktop\amd64\release\bin"
BT_BIN = r"C:\Program Files\Azure Kinect Body Tracking SDK\tools"

if os.path.exists(SDK_BIN):
    os.add_dll_directory(SDK_BIN)
if os.path.exists(BT_BIN):
    os.add_dll_directory(BT_BIN)


# Azure Kinect joint indices mapping to MediaPipe-like format
K4ABT_JOINTS = {
    "PELVIS": 0,
    "SPINE_NAVAL": 1,
    "SPINE_CHEST": 2,
    "NECK": 3,
    "CLAVICLE_LEFT": 4,
    "SHOULDER_LEFT": 5,
    "ELBOW_LEFT": 6,
    "WRIST_LEFT": 7,
    "HAND_LEFT": 8,
    "HANDTIP_LEFT": 9,
    "THUMB_LEFT": 10,
    "CLAVICLE_RIGHT": 11,
    "SHOULDER_RIGHT": 12,
    "ELBOW_RIGHT": 13,
    "WRIST_RIGHT": 14,
    "HAND_RIGHT": 15,
    "HANDTIP_RIGHT": 16,
    "THUMB_RIGHT": 17,
    "HIP_LEFT": 18,
    "KNEE_LEFT": 19,
    "ANKLE_LEFT": 20,
    "FOOT_LEFT": 21,
    "HIP_RIGHT": 22,
    "KNEE_RIGHT": 23,
    "ANKLE_RIGHT": 24,
    "FOOT_RIGHT": 25,
    "HEAD": 26,
    "NOSE": 27,
    "EYE_LEFT": 28,
    "EAR_LEFT": 29,
    "EYE_RIGHT": 30,
    "EAR_RIGHT": 31,
}

# Map Azure Kinect joints to MediaPipe pose indices (33 landmarks)
KINECT_TO_MEDIAPIPE = {
    0: K4ABT_JOINTS["NOSE"],          # MediaPipe index 0: NOSE
    7: K4ABT_JOINTS["EAR_LEFT"],      # MediaPipe index 7: LEFT_EAR
    8: K4ABT_JOINTS["EAR_RIGHT"],     # MediaPipe index 8: RIGHT_EAR
    11: K4ABT_JOINTS["SHOULDER_LEFT"], # MediaPipe index 11: LEFT_SHOULDER
    12: K4ABT_JOINTS["SHOULDER_RIGHT"],# MediaPipe index 12: RIGHT_SHOULDER
    13: K4ABT_JOINTS["ELBOW_LEFT"],    # MediaPipe index 13: LEFT_ELBOW
    14: K4ABT_JOINTS["ELBOW_RIGHT"],   # MediaPipe index 14: RIGHT_ELBOW
    15: K4ABT_JOINTS["WRIST_LEFT"],    # MediaPipe index 15: LEFT_WRIST
    16: K4ABT_JOINTS["WRIST_RIGHT"],   # MediaPipe index 16: RIGHT_WRIST
    17: K4ABT_JOINTS["THUMB_LEFT"],    # MediaPipe index 17: LEFT_PINKY (proxy)
    18: K4ABT_JOINTS["THUMB_RIGHT"],   # MediaPipe index 18: RIGHT_PINKY (proxy)
    19: K4ABT_JOINTS["HANDTIP_LEFT"],  # MediaPipe index 19: LEFT_INDEX (proxy)
    20: K4ABT_JOINTS["HANDTIP_RIGHT"], # MediaPipe index 20: RIGHT_INDEX (proxy)
    23: K4ABT_JOINTS["HIP_LEFT"],      # MediaPipe index 23: LEFT_HIP
    24: K4ABT_JOINTS["HIP_RIGHT"],     # MediaPipe index 24: RIGHT_HIP
}


def skeleton_to_pose_array(skeleton):
    """
    Convert Azure Kinect skeleton to MediaPipe-like pose array
    Returns: List of 33 landmarks, each [x, y, z, confidence]
    """
    pose = [[0.0, 0.0, 0.0, 0.0] for _ in range(33)]
    
    for mp_idx, kinect_idx in KINECT_TO_MEDIAPIPE.items():
        joint = skeleton.joints[kinect_idx]
        pos = joint.position.xyz
        # Normalize confidence from Azure Kinect (0-3) to 0-1 range
        conf_raw = getattr(joint, "confidence_level", 0)
        conf_norm = min(max(conf_raw / 3.0, 0.0), 1.0)
        
        # Convert mm to normalized coordinates (divide by 1000 for meters)
        pose[mp_idx] = [pos.x / 1000.0, pos.y / 1000.0, pos.z / 1000.0, conf_norm]
    
    return pose


def draw_rula_info(image, body_id, rula_left, rula_right, rula_combined, y_offset):
    """
    Draw RULA score information on the image
    """
    # Color coding based on RULA score
    def get_color(score_str):
        try:
            score = int(score_str)
            if score <= 2:
                return (0, 255, 0)  # Green - acceptable
            elif score <= 4:
                return (0, 255, 255)  # Yellow - investigate
            elif score <= 6:
                return (0, 165, 255)  # Orange - investigate and change soon
            else:
                return (0, 0, 255)  # Red - investigate and change immediately
        except:
            return (128, 128, 128)  # Gray for NULL
    
    left_score = rula_left.get('score', 'NULL')
    right_score = rula_right.get('score', 'NULL')
    final_score = rula_combined.get('final_tableC_score', 'NULL')
    
    # Draw header
    cv2.putText(image, f"=== Body {body_id} RULA Analysis ===", 
                (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    y_offset += 35
    
    # Draw left arm info
    left_color = get_color(left_score)
    text = f"Left:  Score={left_score}"
    if 'upper_arm_angle' in rula_left:
        text += f" | Arm={rula_left['upper_arm_angle']}deg"
    if 'wrist_angle' in rula_left:
        text += f" | Wrist={rula_left['wrist_angle']}deg"
    cv2.putText(image, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, left_color, 2)
    y_offset += 30
    
    # Draw right arm info
    right_color = get_color(right_score)
    text = f"Right: Score={right_score}"
    if 'upper_arm_angle' in rula_right:
        text += f" | Arm={rula_right['upper_arm_angle']}deg"
    if 'wrist_angle' in rula_right:
        text += f" | Wrist={rula_right['wrist_angle']}deg"
    cv2.putText(image, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, right_color, 2)
    y_offset += 30
    
    # Draw neck/trunk info
    if 'neck_angle' in rula_left:
        text = f"Neck={rula_left['neck_angle']}deg | Trunk={rula_left.get('trunk_angle', 'NULL')}deg"
        cv2.putText(image, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        y_offset += 30
    
    # Draw final score
    final_color = get_color(final_score)
    cv2.putText(image, f"FINAL RULA SCORE: {final_score}", 
                (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1.2, final_color, 3)
    y_offset += 40
    
    return y_offset


if __name__ == "__main__":

    # 2. 初始化庫 (track_body 必須為 True 以啟動骨架偵測功能)
    pykinect.initialize_libraries(track_body=True)

    # 3. 修改相機配置
    device_config = pykinect.default_configuration
    # 設定彩色影像解析度為 1080P
    device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
    # 設定深度模式為寬視角 (適合近距離偵測)
    device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED

    # 4. 啟動設備
    device = pykinect.start_device(config=device_config)

    # 5. 啟動 Body Tracker
    # 在新版 API 中，直接呼叫 start_body_tracker 即可，它會自動載入最佳配置
    bodyTracker = pykinect.start_body_tracker()

    cv2.namedWindow('RULA Skeleton Analysis', cv2.WINDOW_NORMAL)
    print("Azure Kinect RULA 分析啟動中... 按下 'q' 鍵可退出程式")
    print("=" * 60)

    while True:
        
        # 獲取感測器捕捉數據
        capture = device.update()

        # 獲取骨架幀數據
        body_frame = bodyTracker.update()

        # 獲取彩色影像
        ret, color_image = capture.get_color_image()

        if not ret:
            continue

        # 將骨架畫在彩色影像上
        color_skeleton = body_frame.draw_bodies(color_image, pykinect.K4A_CALIBRATION_TYPE_COLOR)

        # 處理每個偵測到的人並計算 RULA 分數
        num_bodies = body_frame.get_num_bodies()
        
        y_offset = 40
        for i in range(num_bodies):
            # 獲取骨架物件
            skeleton = body_frame.get_body_skeleton(i)
            
            # 轉換為 MediaPipe 格式的 pose array
            pose = skeleton_to_pose_array(skeleton)
            
            # 計算 RULA 分數
            rula_left, rula_right = angle_calc(pose)
            rula_combined = get_best_rula_score(rula_left, rula_right)
            
            # 在畫面上繪製 RULA 資訊
            y_offset = draw_rula_info(color_skeleton, i, rula_left, rula_right, rula_combined, y_offset)
            
            # 在控制台輸出詳細資訊
            print(f"\n[Body {i}]")
            print(f"  Left  - Score: {rula_left.get('score', 'NULL'):>4} | "
                  f"Upper Arm: {str(rula_left.get('upper_arm_angle', 'NULL')):>6} | "
                  f"Wrist: {str(rula_left.get('wrist_angle', 'NULL')):>6}")
            print(f"  Right - Score: {rula_right.get('score', 'NULL'):>4} | "
                  f"Upper Arm: {str(rula_right.get('upper_arm_angle', 'NULL')):>6} | "
                  f"Wrist: {str(rula_right.get('wrist_angle', 'NULL')):>6}")
            print(f"  Posture - Neck: {str(rula_left.get('neck_angle', 'NULL')):>6} | "
                  f"Trunk: {str(rula_left.get('trunk_angle', 'NULL')):>6}")
            print(f"  *** FINAL RULA: {rula_combined.get('final_tableC_score', 'NULL')} ***")

        # 顯示說明
        legend_y = color_skeleton.shape[0] - 100
        cv2.putText(color_skeleton, "RULA Score Guide:", (10, legend_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(color_skeleton, "1-2: Acceptable | 3-4: Investigate", (10, legend_y + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(color_skeleton, "5-6: Change Soon | 7+: Change Immediately", (10, legend_y + 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # 顯示結果
        cv2.imshow('RULA Skeleton Analysis', color_skeleton)    

        # 按下 q 鍵停止
        if cv2.waitKey(1) == ord('q'):  
            break

    # 安全關閉設備
    device.close()
    cv2.destroyAllWindows()
    print("\n程式已安全退出")
