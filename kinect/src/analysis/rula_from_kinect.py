import os
import sys
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import pykinect_azure as pykinect
import hardware.config as kinect_config

# Ensure repo root on sys.path so rula_realtime_app can be imported when running this file directly.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from rula_realtime_app.core.rula_calculator import angle_calc
from rula_realtime_app.core.utils import get_best_rula_score

kinect_config.load_libraries()

def _joint_to_entry(joint) -> List[float]:
    pos = joint.position.xyz
    conf_raw = getattr(joint, "confidence_level", 0)
    conf_norm = min(max(conf_raw / 3.0, 0.0), 1.0)  # Normalize to [0,1]
    return [pos.x, pos.y, pos.z, conf_norm]


def skeleton_to_pose_array(skeleton) -> List[List[float]]:
    pose = [[0.0, 0.0, 0.0, 0.0] for _ in range(33)]
    for mp_idx, kinect_idx in kinect_config.KINECT_TO_MEDIAPIPE.items():
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
