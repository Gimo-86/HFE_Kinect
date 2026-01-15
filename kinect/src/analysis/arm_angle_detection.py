import cv2
import os
import numpy as np
import pykinect_azure as pykinect
import hardware.config as kinect_config


kinect_config.load_libraries()

def safe_angle(v1, v2):
    """安全計算兩向量夾角（度）"""
    v1_norm = np.linalg.norm(v1)
    v2_norm = np.linalg.norm(v2)
    
    if v1_norm < 1e-6 or v2_norm < 1e-6:
        return 0.0
    
    v1_unit = v1 / v1_norm
    v2_unit = v2 / v2_norm
    
    cos_angle = np.clip(np.dot(v1_unit, v2_unit), -1.0, 1.0)
    angle_rad = np.arccos(cos_angle)
    angle_deg = np.degrees(angle_rad)
    
    return angle_deg

def calculate_arm_angles(skeleton):
    """
    計算左右手臂角度（相對於軀幹）
    返回: (left_angle, right_angle, left_confidence, right_confidence)
    """
    # Azure Kinect Body Tracking 關節索引
    PELVIS = 0  # 髖部中心
    SHOULDER_LEFT = 5
    ELBOW_LEFT = 6
    SHOULDER_RIGHT = 12
    ELBOW_RIGHT = 13
    
    # 獲取關節點
    pelvis = skeleton.joints[PELVIS]
    left_shoulder = skeleton.joints[SHOULDER_LEFT]
    left_elbow = skeleton.joints[ELBOW_LEFT]
    right_shoulder = skeleton.joints[SHOULDER_RIGHT]
    right_elbow = skeleton.joints[ELBOW_RIGHT]
    
    # 計算軀幹向量（從肩部中心到髖部中心）
    l_sh_pos = np.array([left_shoulder.position.xyz.x, 
                         left_shoulder.position.xyz.y, 
                         left_shoulder.position.xyz.z])
    r_sh_pos = np.array([right_shoulder.position.xyz.x, 
                         right_shoulder.position.xyz.y, 
                         right_shoulder.position.xyz.z])
    hip_center = np.array([pelvis.position.xyz.x,
                           pelvis.position.xyz.y,
                           pelvis.position.xyz.z])
    
    # 計算肩部中心點
    shoulder_center = (l_sh_pos + r_sh_pos) / 2
    
    # 軀幹向量（肩部 -> 髖部，向下）
    v_trunk = hip_center - shoulder_center
    
    # 提取手臂座標
    l_el_pos = np.array([left_elbow.position.xyz.x, 
                         left_elbow.position.xyz.y, 
                         left_elbow.position.xyz.z])
    r_el_pos = np.array([right_elbow.position.xyz.x, 
                         right_elbow.position.xyz.y, 
                         right_elbow.position.xyz.z])
    
    # 提取置信度
    l_sh_conf = left_shoulder.confidence_level
    l_el_conf = left_elbow.confidence_level
    r_sh_conf = right_shoulder.confidence_level
    r_el_conf = right_elbow.confidence_level
    trunk_conf = min(pelvis.confidence_level,
                     left_shoulder.confidence_level, right_shoulder.confidence_level)
    
    # 計算左手臂角度
    left_angle = 0.0
    left_confidence = min(l_sh_conf, l_el_conf, trunk_conf)
    if left_confidence >= 1:  # 置信度足夠
        # 上臂向量（肩膀 -> 手肘）
        v_left_arm = l_el_pos - l_sh_pos
        # 計算舉手角度（相對於軀幹）
        left_angle = safe_angle(v_left_arm, v_trunk)
    
    # 計算右手臂角度
    right_angle = 0.0
    right_confidence = min(r_sh_conf, r_el_conf, trunk_conf)
    if right_confidence >= 1:  # 置信度足夠
        # 上臂向量（肩膀 -> 手肘）
        v_right_arm = r_el_pos - r_sh_pos
        # 計算舉手角度（相對於軀幹）
        right_angle = safe_angle(v_right_arm, v_trunk)
    
    return left_angle, right_angle, left_confidence, right_confidence

def get_rula_score(angle):
    """根據舉手角度計算 RULA 分數"""
    if angle < 20:
        return 1
    elif angle < 45:
        return 2
    elif angle < 90:
        return 3
    else:
        return 4

if __name__ == "__main__":
    # 2. 初始化庫
    pykinect.initialize_libraries(track_body=True)

    # 3. 修改相機配置
    device_config = pykinect.default_configuration
    device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
    device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED

    # 4. 啟動設備
    device = pykinect.start_device(config=device_config)

    # 5. 啟動 Body Tracker
    bodyTracker = pykinect.start_body_tracker()

    cv2.namedWindow('Arm Angle Detection', cv2.WINDOW_NORMAL)
    print("Azure Kinect 舉手角度偵測啟動中...")
    print("按下 'q' 鍵可退出程式")

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

        # 處理每個偵測到的人
        num_bodies = body_frame.get_num_bodies()
        
        y_offset = 40
        for i in range(num_bodies):
            # 獲取骨架物件
            skeleton = body_frame.get_body_skeleton(i)
            
            # 計算手臂角度
            left_angle, right_angle, left_conf, right_conf = calculate_arm_angles(skeleton)
            
            # 計算 RULA 分數
            left_rula = get_rula_score(left_angle)
            right_rula = get_rula_score(right_angle)
            
            # 顯示左手資訊
            if left_conf >= 1:
                text_left = f"Person {i} - Left Arm: {left_angle:.1f}deg (RULA: {left_rula})"
                cv2.putText(color_skeleton, text_left, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                y_offset += 35
            
            # 顯示右手資訊
            if right_conf >= 1:
                text_right = f"Person {i} - Right Arm: {right_angle:.1f}deg (RULA: {right_rula})"
                cv2.putText(color_skeleton, text_right, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)
                y_offset += 35
            
            y_offset += 10  # 人與人之間的間距

        # 顯示說明文字
        cv2.putText(color_skeleton, "Arm Angle (relative to trunk): 0deg=Along body, 90deg=Horizontal", 
                   (10, color_skeleton.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 顯示結果
        cv2.imshow('Arm Angle Detection', color_skeleton)

        # 按下 q 鍵停止
        if cv2.waitKey(1) == ord('q'):
            break

    # 安全關閉設備
    device.close()
    cv2.destroyAllWindows()
