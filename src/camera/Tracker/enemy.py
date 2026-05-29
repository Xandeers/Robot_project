import cv2
import math
import numpy as np


class EnemyTracker:
    
    def __init__(self, aruco_dict_type=cv2.aruco.DICT_4X4_50, main_id=1, ally_ids=None):
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)

        try:
            self.aruco_params = cv2.aruco.DetectorParameters()
        except AttributeError:
            self.aruco_params = cv2.aruco.DetectorParameters_create()

        self.main_id = main_id
        self.ally_ids = ally_ids if ally_ids is not None else []

    def get_positions(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        corners, ids, _ = cv2.aruco.detectMarkers(
            gray,
            self.aruco_dict,
            parameters=self.aruco_params
        )

        enemies = []
        allies = [] # NOUVEAU

        if ids is not None:
            for i, aruco_id in enumerate(ids.flatten()):
                # Si c'est Idefix, on l'ignore (il a son propre tracker)
                if aruco_id == self.main_id:
                    continue

                c = corners[i][0]

                center_x = int(np.mean(c[:, 0]))
                center_y = int(np.mean(c[:, 1]))

                front_x = int((c[0][0] + c[1][0]) / 2)
                front_y = int((c[0][1] + c[1][1]) / 2)

                angle = math.degrees(
                    math.atan2(front_y - center_y, front_x - center_x)
                )

                robot_data = {
                    "id": int(aruco_id),
                    "center": (center_x, center_y),
                    "front": (front_x, front_y),
                    "angle": angle
                }

                # TRI : Ami ou Ennemi ?
                if aruco_id in self.ally_ids:
                    allies.append(robot_data)
                else:
                    enemies.append(robot_data)

        return allies, enemies

    def draw_entities(self, frame, allies, enemies):
        # Dessiner les alliés (Vert)
        for ally in allies:
            center = ally["center"]
            front = ally["front"]
            cv2.circle(frame, center, 6, (0, 255, 0), -1)
            cv2.arrowedLine(frame, center, front, (0, 255, 0), 3, tipLength=0.3)
            cv2.putText(frame, f"Allie ID {ally['id']}", (center[0] + 15, center[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Dessiner les ennemis (Rouge/Violet)
        for enemy in enemies:
            center = enemy["center"]
            front = enemy["front"]
            cv2.circle(frame, center, 6, (0, 0, 255), -1)
            cv2.arrowedLine(frame, center, front, (0, 0, 255), 3, tipLength=0.3)
            cv2.putText(frame, f"Enemy ID {enemy['id']}", (center[0] + 15, center[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        return frame