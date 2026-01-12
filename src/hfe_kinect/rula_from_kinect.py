import os
import sys
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import pykinect_azure as pykinect

# Ensure repo root on sys.path so rula_realtime_app can be imported when running this file directly.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from rula_realtime_app.core.rula_calculator import angle_calc
from rula_realtime_app.core.utils import get_best_rula_score

# Azure Kinect SDK + Body Tracking SDK DLL paths (update if installed elsewhere).
SDK_BIN = r"C:\Program Files\Azure Kinect SDK v1.4.1\sdk\windows-desktop\amd64\release\bin"
BT_BIN = r"C:\Program Files\Azure Kinect Body Tracking SDK\tools"

if os.path.exists(SDK_BIN):
    os.add_dll_directory(SDK_BIN)
if os.path.exists(BT_BIN):
    os.add_dll_directory(BT_BIN)

# Azure Kinect joint indices (K4ABT)
K4ABT = {
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

# Map Azure Kinect joints into a MediaPipe-like pose array (33 entries, each [x, y, z, conf]).
# Only the indices used by rula_calculator need to be populated; others stay zeros.
KINECT_TO_MEDIAPIPE = {
    0: K4ABT["NOSE"],          # NOSE
    7: K4ABT["EAR_LEFT"],      # LEFT EAR
    8: K4ABT["EAR_RIGHT"],     # RIGHT EAR
    11: K4ABT["SHOULDER_LEFT"],
    12: K4ABT["SHOULDER_RIGHT"],
    13: K4ABT["ELBOW_LEFT"],
    14: K4ABT["ELBOW_RIGHT"],
    15: K4ABT["WRIST_LEFT"],
    16: K4ABT["WRIST_RIGHT"],
    # Use thumb as pinky proxy and handtip as index proxy to satisfy hand center calc.
    17: K4ABT["HAND_LEFT"],   # LEFT WRIST (equivlalent mid point calculations later)
    18: K4ABT["HAND_RIGHT"],  # RIGHT WRIST (equivalent mid point calc later)
    19: K4ABT["HAND_LEFT"],   # LEFT WRIST (equivalent mid point calc later)
    20: K4ABT["HAND_RIGHT"],  # RIGHT WRIST (equivalent mid point calc later)
    23: K4ABT["HIP_LEFT"],
    24: K4ABT["HIP_RIGHT"],
}


def _joint_to_entry(joint) -> List[float]:
    pos = joint.position.xyz
    conf_raw = getattr(joint, "confidence_level", 0)
    conf_norm = min(max(conf_raw / 3.0, 0.0), 1.0)  # Normalize to [0,1]
    return [pos.x, pos.y, pos.z, conf_norm]


def skeleton_to_pose_array(skeleton) -> List[List[float]]:
    pose = [[0.0, 0.0, 0.0, 0.0] for _ in range(33)]
    for mp_idx, kinect_idx in KINECT_TO_MEDIAPIPE.items():
        joint = skeleton.joints[kinect_idx]
        pose[mp_idx] = _joint_to_entry(joint)
    return pose


def compute_rula_for_bodies(body_frame, color_image) -> Tuple[np.ndarray, list]:
    num_bodies = body_frame.get_num_bodies()
    results = []
    overlay = color_image.copy()

    for i in range(num_bodies):
        skeleton = body_frame.get_body_skeleton(i)
        pose = skeleton_to_pose_array(skeleton)

        left, right = angle_calc(pose)
        combined = get_best_rula_score(left, right)
        results.append({"id": i, "left": left, "right": right, "final": combined})

        # Render per-person info on the overlay.
        y = 40 + i * 60
        text = (
            f"Body {i} | L:{left.get('score', 'NULL')} R:{right.get('score', 'NULL')} "
            f"Final:{combined.get('final_tableC_score', 'NULL')}"
        )
        cv2.putText(overlay, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    return overlay, results


def main():
    pykinect.initialize_libraries(track_body=True)

    device_config = pykinect.default_configuration
    device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
    device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED

    device = pykinect.start_device(config=device_config)
    body_tracker = pykinect.start_body_tracker()

    cv2.namedWindow("RULA Score", cv2.WINDOW_NORMAL)
    print("Azure Kinect RULA scoring... press 'q' to quit")

    while True:
        capture = device.update()
        body_frame = body_tracker.update()

        ret, color_image = capture.get_color_image()
        if not ret:
            continue

        # Draw skeletons in color camera space.
        color_skeleton = body_frame.draw_bodies(color_image, pykinect.K4A_CALIBRATION_TYPE_COLOR)

        # Compute RULA and render scores.
        overlay, results = compute_rula_for_bodies(body_frame, color_image)
        blended = cv2.addWeighted(color_skeleton, 0.7, overlay, 0.3, 0)

        # Optional: log to console.
        if results:
            for res in results:
                print(
                    f"Body {res['id']} -> L:{res['left'].get('score')} "
                    f"R:{res['right'].get('score')} Final:{res['final'].get('final_tableC_score')}"
                )

        cv2.imshow("RULA Score", blended)
        if cv2.waitKey(1) == ord('q'):
            break

    device.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
