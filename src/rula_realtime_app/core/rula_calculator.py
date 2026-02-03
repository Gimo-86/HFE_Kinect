"""
RULA 計算核心模組
負責角度計算和 RULA 評分
"""

import numpy as np
from .rula_tables import TABLE_A_DATA, TABLE_B_DATA, TABLE_C_DATA
from .utils import safe_angle, safe_unit_vector, check_confidence
from .config import RULA_CONFIG, TOLERANCE_ANGLE, USE_PREVIOUS_FRAME_ON_LOW_CONFIDENCE

def rula_risk(point_score, wrist, trunk, upper_Shoulder, lower_Limb, neck,
              wrist_twist, legs, muscle_use_a, muscle_use_b, force_load_a, force_load_b):
    """依 RULA A/B/C 三表計算總分"""
    rula = {'score': 'NULL'}
    if wrist!=0 and trunk!=0 and upper_Shoulder!=0 and lower_Limb!=0 and neck!=0 and wrist_twist!=0:
        # Table A（上臂/前臂/手腕）
        col_name = f"{wrist}WT{wrist_twist}"
        if (upper_Shoulder, lower_Limb) in TABLE_A_DATA:
            taval = TABLE_A_DATA[(upper_Shoulder, lower_Limb)][col_name]
            point_score['posture_score_a'] = str(taval)

            taval = taval + muscle_use_a + force_load_a
            point_score['wrist_and_arm_score'] = str(taval)

            # Table B（頸/軀幹/腿）
            col_name = f"{trunk}{legs}"
            if neck in TABLE_B_DATA:
                tbval = TABLE_B_DATA[neck][col_name]
                point_score['posture_score_b'] = str(tbval)

                tbval = tbval + force_load_b + muscle_use_b
                point_score['neck_trunk_leg_score'] = str(tbval)

                # Table C（A×B 合成）
                if taval >= 8: taval = 8
                if tbval >= 7: tbval = 7

                if taval in TABLE_C_DATA and tbval in TABLE_C_DATA[taval]:
                    tcval = TABLE_C_DATA[taval][tbval]
                    rula['score'] = str(tcval)
    return rula, point_score
# import pprint
def rula_score_side(pose, side: str, previous_scores=None):
    """
    計算單側（Left/Right）RULA 分數
    """
    point_score = {}
    angle_data = {}
    # print(f"[DEBUG] 使用中的 RULA_CONFIG ({side}):")
    # pprint.pprint(RULA_CONFIG)   # 清楚輸出 dict
    # MediaPipe Pose 索引
    L_SHOULDER, R_SHOULDER = 11, 12
    L_ELBOW, R_ELBOW = 13, 14
    L_WRIST, R_WRIST = 15, 16
    L_PINKY, R_PINKY = 17, 18
    L_INDEX, R_INDEX = 19, 20
    L_EAR, R_EAR = 7, 8
    L_HIP, R_HIP = 23, 24

    # 身體中線計算
    SHO_C = np.array([(pose[L_SHOULDER][0] + pose[R_SHOULDER][0])/2,
                      (pose[L_SHOULDER][1] + pose[R_SHOULDER][1])/2,
                      (pose[L_SHOULDER][2] + pose[R_SHOULDER][2])/2])
    HIP_C = np.array([(pose[L_HIP][0] + pose[R_HIP][0])/2,
                      (pose[L_HIP][1] + pose[R_HIP][1])/2,
                      (pose[L_HIP][2] + pose[R_HIP][2])/2])
    v_body = HIP_C - SHO_C

    # 頭部中心計算
    HEAD_C = np.array([(pose[L_EAR][0] + pose[R_EAR][0])/2,
                       (pose[L_EAR][1] + pose[R_EAR][1])/2,
                       (pose[L_EAR][2] + pose[R_EAR][2])/2])

    # 選擇該側的關鍵點
    if side == 'Left':
        SH = np.array([pose[L_SHOULDER][0], pose[L_SHOULDER][1], pose[L_SHOULDER][2]])
        EL = np.array([pose[L_ELBOW][0], pose[L_ELBOW][1], pose[L_ELBOW][2]])
        WR = np.array([pose[L_WRIST][0], pose[L_WRIST][1], pose[L_WRIST][2]])
        INDEX = np.array([pose[L_INDEX][0], pose[L_INDEX][1], pose[L_INDEX][2]])
        PINKY = np.array([pose[L_PINKY][0], pose[L_PINKY][1], pose[L_PINKY][2]])
        arm_indices = [L_SHOULDER, L_ELBOW, L_WRIST, L_INDEX, L_PINKY]
    else:
        SH = np.array([pose[R_SHOULDER][0], pose[R_SHOULDER][1], pose[R_SHOULDER][2]])
        EL = np.array([pose[R_ELBOW][0], pose[R_ELBOW][1], pose[R_ELBOW][2]])
        WR = np.array([pose[R_WRIST][0], pose[R_WRIST][1], pose[R_WRIST][2]])
        INDEX = np.array([pose[R_INDEX][0], pose[R_INDEX][1], pose[R_INDEX][2]])
        PINKY = np.array([pose[R_PINKY][0], pose[R_PINKY][1], pose[R_PINKY][2]])
        arm_indices = [R_SHOULDER, R_ELBOW, R_WRIST, R_INDEX, R_PINKY]

    # 檢查該側手臂關鍵點置信度
    arm_has_confidence = check_confidence(pose, arm_indices)

    # 手掌中心
    if arm_has_confidence:
        HAND_C = (INDEX + PINKY) / 2
    else:
        HAND_C = None

    # A-1: Upper Arm（上臂屈伸角）
    upper_arm_indices = [L_SHOULDER, L_ELBOW] if side == 'Left' else [R_SHOULDER, R_ELBOW]
    if check_confidence(pose, upper_arm_indices):
        v_sh_el = EL - SH
        theta_upper = safe_angle(v_sh_el, v_body)
        angle_data['upper_arm_angle'] = round(theta_upper, 2)

        if theta_upper < 20:
            upper_arm_score = 1
        elif theta_upper < 45:
            upper_arm_score = 2
        elif theta_upper < 90:
            upper_arm_score = 3
        else:
            upper_arm_score = 4
    else:
        angle_data['upper_arm_angle'] = 'NULL'
        if USE_PREVIOUS_FRAME_ON_LOW_CONFIDENCE and previous_scores is not None:
            upper_arm_score = previous_scores.get('upper_arm_score', 1) if isinstance(previous_scores, dict) else 1
        else:
            upper_arm_score = 1

    point_score['upper_arm'] = upper_arm_score
    point_score['upper_arm_adjustment'] = 0

    # A-2: Lower Arm（肘內角）
    lower_arm_indices = [L_ELBOW, L_WRIST] if side == 'Left' else [R_ELBOW, R_WRIST]
    if check_confidence(pose, lower_arm_indices + upper_arm_indices):
        v_el_wr = WR - EL
        v_el_sh = SH - EL
        theta_elbow = safe_angle(v_el_wr, v_el_sh)
        angle_data['lower_arm_angle'] = round(theta_elbow, 2)

        if 60 <= theta_elbow <= 100:
            lower_arm_score = 1
        else:
            lower_arm_score = 2
    else:
        angle_data['lower_arm_angle'] = 'NULL'
        if USE_PREVIOUS_FRAME_ON_LOW_CONFIDENCE and previous_scores is not None:
            lower_arm_score = previous_scores.get('lower_arm_score', 1) if isinstance(previous_scores, dict) else 1
        else:
            lower_arm_score = 1

    point_score['lower_arm'] = lower_arm_score
    point_score['lower_arm_adjustment'] = 0

    # A-3: Wrist Position（手腕屈伸角）- 根據 pipeline.md 方法
    wrist_indices = [L_WRIST, L_INDEX, L_PINKY] if side == 'Left' else [R_WRIST, R_INDEX, R_PINKY]
    if HAND_C is not None and check_confidence(pose, wrist_indices + lower_arm_indices):
        # 步驟1：計算前臂軸向量（肘→腕）
        forearm_vector = WR - EL  # 前臂軸（肘→腕向量）

        # 步驟2：計算手掌軸向量（腕→手心）
        hand_vector = HAND_C - WR  # 手掌軸（腕→手心向量）

        # 步驟3：計算兩軸夾角
        theta_wrist = safe_angle(forearm_vector, hand_vector)
        angle_data['wrist_angle'] = round(theta_wrist, 2)

        # RULA 分數規則（符合 pipeline.md）
        if theta_wrist <= TOLERANCE_ANGLE:  # ≤ 5°
            wrist_score = 1
        elif theta_wrist <= 15:  # ≤ 15°
            wrist_score = 2
        else:  # > 15°
            wrist_score = 3
    else:
        angle_data['wrist_angle'] = 'NULL'
        if USE_PREVIOUS_FRAME_ON_LOW_CONFIDENCE and previous_scores is not None:
            wrist_score = previous_scores.get('wrist_score', 1) if isinstance(previous_scores, dict) else 1
        else:
            wrist_score = 1

    point_score['wrist'] = wrist_score
    point_score['wrist_adjustment'] = 0

    # B-1: Neck（頸角）- 使用 pipeline.md 中的鼻子-耳朵方法
    head_indices = [L_EAR, R_EAR]
    if check_confidence(pose, head_indices + [L_SHOULDER, R_SHOULDER]):
        t = SHO_C - HIP_C  # 軀幹向量（髖→肩）
        n = HEAD_C - SHO_C  # 頸部向量（肩→頭）

        # 計算基本角度（0-180度）
        theta_neck = safe_angle(t, n)

        # 判斷前後方向：使用鼻子與兩耳中心的Y軸差異（pipeline.md方法）
        NOSE = 0  # MediaPipe 鼻子索引
        neck_forward = True  # 預設為前屈

        # 檢查鼻子和兩耳的置信度
        if (len(pose) > NOSE and len(pose[NOSE]) > 3 and pose[NOSE][3] > 0.5 and  # 鼻子置信度
            pose[L_EAR][3] > 0.5 and pose[R_EAR][3] > 0.5):  # 兩耳置信度

            # 獲取關鍵點座標
            nose_pos = np.array([pose[NOSE][0], pose[NOSE][1], pose[NOSE][2]])
            l_ear_pos = np.array([pose[L_EAR][0], pose[L_EAR][1], pose[L_EAR][2]])
            r_ear_pos = np.array([pose[R_EAR][0], pose[R_EAR][1], pose[R_EAR][2]])

            # 計算兩耳中心點
            ear_center = (l_ear_pos + r_ear_pos) / 2

            # Y軸差異判斷（MediaPipe座標系：Y向下為正）
            nose_ear_y_diff = nose_pos[1] - ear_center[1]

            # 判斷邏輯：
            # 前屈（低頭）：鼻子比耳朵低 → nose_ear_y_diff > 0 → 正角度
            # 後仰（抬頭）：鼻子比耳朵高 → nose_ear_y_diff < 0 → 負角度
            if nose_ear_y_diff < -0.01:  # 鼻子比耳朵高，後仰
                neck_forward = False
            elif nose_ear_y_diff > 0.01:  # 鼻子比耳朵低，前屈
                neck_forward = True
            else:  # 中性範圍，預設前屈
                neck_forward = True
        else:
            # 備用方法：使用頸向量的Y分量
            head_y_component = -n[1]  # 頸向量Y分量的負值
            if head_y_component > 0.1:
                neck_forward = True
            elif head_y_component < -0.1:
                neck_forward = False
            else:
                neck_forward = True  # 預設前屈

        # 根據前後方向決定角度符號
        if not neck_forward:  # 後仰
            signed_neck_angle = -theta_neck  # 後仰顯示負角度
        else:  # 前屈或中性
            signed_neck_angle = theta_neck   # 前屈顯示正角度

        angle_data['neck_angle'] = round(signed_neck_angle, 2)

        # RULA 評分基於絕對角度值（符合 pipeline.md 規則）
        abs_theta_neck = abs(signed_neck_angle)

        # RULA分數規則
        if not neck_forward and abs_theta_neck > 5:  # 後仰且角度 > 5°
            neck_score = 4  # 後仰特殊情況
        elif abs_theta_neck < 10:
            neck_score = 1
        elif abs_theta_neck < 20:
            neck_score = 2
        else:  # abs_theta_neck ≥ 20°
            neck_score = 3
    else:
        angle_data['neck_angle'] = 'NULL'
        if USE_PREVIOUS_FRAME_ON_LOW_CONFIDENCE and previous_scores is not None:
            neck_score = previous_scores.get('neck_score', 1) if isinstance(previous_scores, dict) else 1
        else:
            neck_score = 1

    point_score['neck'] = neck_score
    point_score['neck_adjustment'] = 0

    # B-2: Trunk（軀幹角）
    trunk_indices = [L_SHOULDER, R_SHOULDER, L_HIP, R_HIP]
    if check_confidence(pose, trunk_indices):
        t = SHO_C - HIP_C  # 軀幹向量（髖→肩，向上）
        VERTICAL_UP = np.array([0, -1, 0])  # 垂直向上參考向量（Kinect/MediaPipe 坐標系）
        theta_trunk = safe_angle(t, VERTICAL_UP)  # 計算軀幹與垂直方向的夾角
        angle_data['trunk_angle'] = round(theta_trunk, 2)

        if theta_trunk <= TOLERANCE_ANGLE:
            trunk_score = 1
        elif theta_trunk < 20:
            trunk_score = 2
        elif theta_trunk < 60:
            trunk_score = 3
        else:
            trunk_score = 4
    else:
        angle_data['trunk_angle'] = 'NULL'
        if USE_PREVIOUS_FRAME_ON_LOW_CONFIDENCE and previous_scores is not None:
            trunk_score = previous_scores.get('trunk_score', 1) if isinstance(previous_scores, dict) else 1
        else:
            trunk_score = 1

    point_score['trunk'] = trunk_score
    point_score['trunk_adjustment'] = 0

    # 固定/預設參數（從設定檔取得）
    wrist_twist = RULA_CONFIG['wrist_twist']
    legs = RULA_CONFIG['legs']
    muscle_use_a = RULA_CONFIG['muscle_use_a']
    muscle_use_b = RULA_CONFIG['muscle_use_b']
    force_load_a = RULA_CONFIG['force_load_a']
    force_load_b = RULA_CONFIG['force_load_b']

    point_score['wrist_twist'] = wrist_twist
    point_score['legs'] = legs
    point_score['muscle_use_a'] = muscle_use_a
    point_score['force_load_a'] = force_load_a
    point_score['force_load_b'] = force_load_b
    point_score['muscle_use_b'] = muscle_use_b

    # 儲存各部位分數以供下次低置信度時使用
    point_score['upper_arm_score'] = upper_arm_score
    point_score['lower_arm_score'] = lower_arm_score
    point_score['wrist_score'] = wrist_score
    point_score['neck_score'] = neck_score
    point_score['trunk_score'] = trunk_score

    # 計算最終 RULA 分數
    try:
        rula, _ = rula_risk(
            point_score, wrist_score, trunk_score, upper_arm_score, lower_arm_score, neck_score,
            wrist_twist, legs, muscle_use_a, muscle_use_b, force_load_a, force_load_b
        )
        rula.update(point_score)
        rula.update(angle_data)
    except Exception as e:
        print(f"RULA計算錯誤 ({side}): {e}")
        rula = {'score': '1'}
        rula.update(point_score)
        rula.update(angle_data)

    return rula

def angle_calc(pose, previous_left=None, previous_right=None):
    """計算左右側 RULA 分數"""
    try:
        if not pose or len(pose) < 33:
            return ({"score": "NULL"}, {"score": "NULL"})

        rula_left = rula_score_side(pose, 'Left', previous_left)
        rula_right = rula_score_side(pose, 'Right', previous_right)

        return (rula_left, rula_right)
    except Exception as e:
        print(f"angle_calc 錯誤: {e}")
        return ({"score": "NULL"}, {"score": "NULL"})
