import socket
import cv2
import numpy as np
import struct

from src.camera.terrain import TerrainIMG
from src.camera.Tracker.ball import BallTracker
from src.camera.Tracker.robot import RobotTracker
from src.camera.Tracker.enemy import EnemyTracker

from src.terrain.graph import Graph


# --- Configuration Réseau ---
ip = ""
port = 8080
MaximumPacketSize = 1400

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, port))
print("Listening for UDP frames...")

# --- Initialisation des modules ---
terrain_manager = TerrainIMG(num_zones=2, points_per_zone=8)
ball_tracker = BallTracker()
robot_tracker = RobotTracker(robot_id=1)
enemy_tracker = EnemyTracker(ally_id=1)

mon_graph = Graph(x_widthCM=301, y_lengthCM=390)
mon_graph.set_cage(x_min=100, x_max=200, y_min=370, y_max=390)

is_calibrated = False

POINTS_REELS_CM = [
    # --- ZONE 1 ---
    (0, 195),
    (150.5, 195),
    (301, 195),
    (301, 292.5),
    (301, 390),
    (150.5, 390),
    (0, 390),
    (0, 292.5),

    # --- ZONE 2 ---
    (301, 195),
    (150.5, 195),
    (0, 195),
    (0, 97.5),
    (0, 0),
    (150.5, 0),
    (301, 0),
    (301, 97.5)
]

# --- Calibration initiale depuis JSON ---
if len(terrain_manager.points) == 16:
    try:
        mon_graph.matriceConfig(
            terrain_manager.points[0:8],
            POINTS_REELS_CM[0:8],
            id_cam=1
        )
        mon_graph.matriceConfig(
            terrain_manager.points[8:16],
            POINTS_REELS_CM[8:16],
            id_cam=2
        )
        is_calibrated = True
        print("Succes : les deux matrices sont calibrees depuis le JSON.")
    except Exception as e:
        print("Erreur calibration initiale : %s" % e)


# --- Fenêtre vidéo ---
window_name = "Received Frame"
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, terrain_manager.mouse_callback)

data_buffer = {}
current_frame_id = -1

messageHeader = 4
headerSize = 8


while True:
    try:
        packet, addr = sock.recvfrom(MaximumPacketSize)
        packet_id, frame_id = struct.unpack("II", packet[:headerSize])
        payload = packet[headerSize:]

        if frame_id != current_frame_id:

            if current_frame_id != -1 and current_frame_id + 1 == frame_id:

                full_data = b"".join(
                    [data_buffer[i] for i in sorted(data_buffer)]
                )

                frame_data = full_data[messageHeader:]
                frame_buffer = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(frame_buffer, 1)

                if frame is not None:

                    # --- 1. Calibration ---
                    if len(terrain_manager.points) < 16:
                        cv2.putText(
                            frame,
                            "Calibration: %s/16" % len(terrain_manager.points),
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 0, 255),
                            2
                        )
                        is_calibrated = False

                    elif not is_calibrated:
                        try:
                            mon_graph.matriceConfig(
                                terrain_manager.points[0:8],
                                POINTS_REELS_CM[0:8],
                                id_cam=1
                            )
                            mon_graph.matriceConfig(
                                terrain_manager.points[8:16],
                                POINTS_REELS_CM[8:16],
                                id_cam=2
                            )
                            is_calibrated = True
                            print("Succes : matrices calculees apres clics.")
                        except Exception as e:
                            print("Erreur matrice : %s" % e)

                    # --- 2. Tracking vidéo ---
                    ball_info = ball_tracker.get_position(frame)
                    frame = ball_tracker.draw_ball(frame, ball_info)

                    robot_info = robot_tracker.getposition(frame)
                    frame = robot_tracker.drawRobot(frame, robot_info)

                    enemies_info = enemy_tracker.get_positions(frame)
                    frame = enemy_tracker.draw_enemies(frame, enemies_info)

                    frame = terrain_manager.draw_zones(frame)

                    coord_balle_cm = None
                    coord_robot_cm = None
                    coord_enemies_cm = []

                    # --- 3. Conversion robot en cm ---
                    if robot_info and is_calibrated:
                        pos_robot = robot_info["center"]

                        if terrain_manager.is_in_zone(pos_robot, 0):
                            coord_robot_cm = mon_graph.convertir_pixel_to_graph(
                                pos_robot[0],
                                pos_robot[1],
                                cam_id=1
                            )

                        elif terrain_manager.is_in_zone(pos_robot, 1):
                            coord_robot_cm = mon_graph.convertir_pixel_to_graph(
                                pos_robot[0],
                                pos_robot[1],
                                cam_id=2
                            )

                    # --- 4. Conversion ennemis en cm ---
                    if enemies_info and is_calibrated:
                        for enemy in enemies_info:
                            pos_enemy = enemy["center"]
                            coord_enemy_cm = None

                            if terrain_manager.is_in_zone(pos_enemy, 0):
                                coord_enemy_cm = mon_graph.convertir_pixel_to_graph(
                                    pos_enemy[0],
                                    pos_enemy[1],
                                    cam_id=1
                                )

                            elif terrain_manager.is_in_zone(pos_enemy, 1):
                                coord_enemy_cm = mon_graph.convertir_pixel_to_graph(
                                    pos_enemy[0],
                                    pos_enemy[1],
                                    cam_id=2
                                )

                            if coord_enemy_cm is not None:
                                coord_enemies_cm.append({
                                    "id": enemy["id"],
                                    "coord": coord_enemy_cm
                                })

                                cv2.putText(
                                    frame,
                                    "ENNEMI %s : %.1fcm %.1fcm" % (
                                        enemy["id"],
                                        coord_enemy_cm.x,
                                        coord_enemy_cm.y
                                    ),
                                    (20, 150 + 30 * len(coord_enemies_cm)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6,
                                    (0, 0, 255),
                                    2
                                )

                    # --- 5. Conversion balle en cm ---
                    if ball_info and is_calibrated:
                        pos_balle = ball_info["center"]

                        if terrain_manager.is_in_zone(pos_balle, 0):
                            coord_balle_cm = mon_graph.convertir_pixel_to_graph(
                                pos_balle[0],
                                pos_balle[1],
                                cam_id=1
                            )

                            cv2.putText(
                                frame,
                                "BALLE ZONE 1",
                                (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (255, 0, 0),
                                2
                            )

                        elif terrain_manager.is_in_zone(pos_balle, 1):
                            coord_balle_cm = mon_graph.convertir_pixel_to_graph(
                                pos_balle[0],
                                pos_balle[1],
                                cam_id=2
                            )

                            cv2.putText(
                                frame,
                                "BALLE ZONE 2",
                                (50, pos_balle[1] - 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (0, 255, 255),
                                2
                            )

                        else:
                            cv2.putText(
                                frame,
                                "BALLE HORS ZONE",
                                (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (255, 255, 255),
                                2
                            )

                        if coord_balle_cm is not None:
                            texte_cm = "%.1fcm, %.1fcm" % (
                                coord_balle_cm.x,
                                coord_balle_cm.y
                            )

                            cv2.putText(
                                frame,
                                texte_cm,
                                (pos_balle[0] - 20, pos_balle[1] - 20),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 255, 0),
                                2
                            )

                            if mon_graph.is_but(coord_balle_cm):
                                cv2.putText(
                                    frame,
                                    "!!! BUT !!!",
                                    (200, 200),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    3,
                                    (0, 0, 255),
                                    5
                                )
                                print("La balle est dans la cage !")

                    # --- 6. Minimap radar ---
                    carte_radar = mon_graph.afficher_minimap(
                        coord_balle_cm=coord_balle_cm,
                        coord_robot_cm=coord_robot_cm
                    )

                    cv2.imshow("Radar Terrain Physique (cm)", carte_radar)

                    # --- 7. Vidéo originale ---
                    cv2.imshow(window_name, frame)

                    ch = chr(cv2.waitKey(1) & 0xFF)
                    if ch == "q" or ch == "Q":
                        break

            data_buffer = {}
            current_frame_id = frame_id

        data_buffer[packet_id] = payload

    except socket.error:
        continue


sock.close()
cv2.destroyAllWindows()