import cv2
import os
import pykinect_azure as pykinect

# 1. 確保 DLL 路徑正確 (請確認這兩個路徑與您電腦中的實際路徑相符)
SDK_BIN = r"C:\Program Files\Azure Kinect SDK v1.4.1\sdk\windows-desktop\amd64\release\bin"
BT_BIN = r"C:\Program Files\Azure Kinect Body Tracking SDK\tools"

if os.path.exists(SDK_BIN):
    os.add_dll_directory(SDK_BIN)
if os.path.exists(BT_BIN):
    os.add_dll_directory(BT_BIN)

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

    cv2.namedWindow('Color image with skeleton', cv2.WINDOW_NORMAL)
    print("Azure Kinect 啟動中... 按下 'q' 鍵可退出程式")

    while True:
        
        # 獲取感測器捕捉數據
        capture = device.update()

        # 獲取骨架幀數據
        body_frame = bodyTracker.update()

        # 在迴圈中處理 body_frame
        num_bodies = body_frame.get_num_bodies()  # 偵測到的人數

        body_info = []  # 儲存每個人的資訊
        for i in range(num_bodies):
            # 獲取第 i 個人的骨架物件
            skeleton = body_frame.get_body_skeleton(i)
            
            # 獲取「右手腕」關節點 (對應索引 14)
            # 你可以使用內建常數: pykinect.K4ABT_JOINT_WRIST_RIGHT
            right_wrist = skeleton.joints[14]
            
            # 提取 3D 物理座標 (mm)
            pos = right_wrist.position
            confidence = right_wrist.confidence_level
            body_info.append((i, pos.xyz.x, pos.xyz.y, pos.xyz.z, confidence))

        # 獲取彩色影像
        ret, color_image = capture.get_color_image()

        if not ret:
            continue

        # 6. 將骨架畫在彩色影像上
        # 關鍵點：加入 pykinect.K4A_CALIBRATION_TYPE_COLOR 以修正鏡頭視差導致的偏移
        color_skeleton = body_frame.draw_bodies(color_image, pykinect.K4A_CALIBRATION_TYPE_COLOR)

        # 在畫面上顯示座標資訊
        y_offset = 30
        for i, x, y, z, conf in body_info:
            text = f"Body {i} - Wrist: X={x:.1f}, Y={y:.1f}, Z={z:.1f}, Conf={conf}"
            cv2.putText(color_skeleton, text, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            y_offset += 30

        # 顯示結果
        cv2.imshow('Color image with skeleton', color_skeleton)    

        # 按下 q 鍵停止
        if cv2.waitKey(1) == ord('q'):  
            break

    # 安全關閉設備
    device.close()
    cv2.destroyAllWindows()