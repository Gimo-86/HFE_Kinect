"""
工具函數模組
包含通用的數學計算和輔助函數
"""

import numpy as np
from .video_config import MIN_CONFIDENCE

def safe_unit_vector(v):
    """安全的單位化向量，避免零長度向量"""
    v = np.array(v)
    norm = np.linalg.norm(v)
    if norm < 1e-6:
        return np.array([0, 0, 0])
    return v / norm

def safe_angle(u, v):
    """安全的向量夾角計算（0-180度），避免數值誤差"""
    u_unit = safe_unit_vector(u)
    v_unit = safe_unit_vector(v)
    
    # 檢查零向量
    if np.linalg.norm(u_unit) < 1e-6 or np.linalg.norm(v_unit) < 1e-6:
        return 0.0
    
    dot_product = np.clip(np.dot(u_unit, v_unit), -1.0, 1.0)
    return np.degrees(np.arccos(dot_product))

def check_confidence(landmarks, indices, min_conf=None):
    """檢查指定索引的關鍵點是否都有足夠的置信度"""
    if min_conf is None:
        min_conf = MIN_CONFIDENCE
    for idx in indices:
        if idx >= len(landmarks) or landmarks[idx][3] < min_conf:
            return False
    return True

def get_best_rula_score(rula_left, rula_right):
    """取左右手中較高的分數作為最終評估"""
    result = {
        "left": rula_left,
        "right": rula_right,
        "final_tableC_score": "NULL"
    }
    
    try:
        left_score = int(rula_left.get('score', 0)) if rula_left.get('score') != "NULL" else None
        right_score = int(rula_right.get('score', 0)) if rula_right.get('score') != "NULL" else None
        
        if left_score is not None and right_score is not None:
            if left_score >= right_score:
                result["final_tableC_score"] = str(left_score)
            else:
                result["final_tableC_score"] = str(right_score)
        elif left_score is not None:
            result["final_tableC_score"] = str(left_score)
        elif right_score is not None:
            result["final_tableC_score"] = str(right_score)
    except Exception as e:
        print(f"get_best_rula_score 錯誤: {e}")
    
    return result
