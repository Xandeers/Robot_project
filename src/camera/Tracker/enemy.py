import cv2
import math
import numpy as np


class EnemyTracker:
    def __init__(self, aruco_dict_type=cv2.aruco.DICT_4X4_50, ally_id=1):
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)

        try:
            self.aruco_params = cv2.aruco.DetectorParameters()
        except AttributeError:
            self.aruco_params = cv2.aruco.DetectorParameters_create()

        self.ally_id = ally_id

    def get_positions(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        corners, ids, _ = cv2.aruco.detectMarkers(
            gray,
            self.aruco_dict,
            parameters=self.aruco_params
        )

        enemies = []

        if ids is not None:
            for i, aruco_id in enumerate(ids.flatten()):
                if aruco_id == self.ally_id:
                    continue

                c = corners[i][0]

                center_x = int(np.mean(c[:, 0]))
                center_y = int(np.mean(c[:, 1]))

                front_x = int((c[0][0] + c[1][0]) / 2)
                front_y = int((c[0][1] + c[1][1]) / 2)

                angle = math.degrees(
                    math.atan2(front_y - center_y, front_x - center_x)
                )

                enemies.append({
                    "id": int(aruco_id),
                    "center": (center_x, center_y),
                    "front": (front_x, front_y),
                    "angle": angle
                })

        return enemies

    def draw_enemies(self, frame, enemies):
        for enemy in enemies:
            center = enemy["center"]
            front = enemy["front"]

            cv2.circle(frame, center, 6, (0, 0, 255), -1)
            cv2.arrowedLine(frame, center, front, (0, 0, 255), 3, tipLength=0.3)

            cv2.putText(
                frame,
                "Enemy ID %s" % enemy["id"],
                (center[0] + 15, center[1]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

        return frame