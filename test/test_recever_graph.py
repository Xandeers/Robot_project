import socket
import cv2
import numpy as np
import struct

from src.camera.terrain import TerrainIMG
from src.camera.Tracker.ball import BallTracker
from src.camera.Tracker.robot import RobotTracker

from src.terrain.graph import Graph 


ip = ""  
port = 8080
MaximumPacketSize = 1400

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, port))
print("Listening for UDP frames...")


terrain_manager = TerrainIMG(num_zones=2, points_per_zone=8)
ball_tracker = BallTracker()
robot_tracker = RobotTracker(robot_id=1)
mon_graph = Graph(x_widthCM=301, y_lengthCM=390)
mon_graph.set_cage(x_min=100, x_max=200, y_min=370, y_max=390)
is_calibrated = False


POINTS_REELS_CM = [
    # --- ZONE 1 (Flux Caméra 1) ---
    (0, 195),      # 1
    (150.5, 195),  # 2
    (301, 195),    # 3
    (301, 292.5),  # 4
    (301, 390),    # 5
    (150.5, 390),  # 6
    (0, 390),      # 7
    (0, 292.5),    # 8

    # --- ZONE 2 (Flux Caméra 2 - Inversée) ---
    (301, 195),    # 9
    (150.5, 195),  # 10
    (0, 195),      # 11
    (0, 97.5),     # 12
    (0, 0),        # 13
    (150.5, 0),    # 14
    (301, 0),      # 15
    (301, 97.5)    # 16
]

if len(terrain_manager.points) == 16:
    try:
        mon_graph.matriceConfig(terrain_manager.points[0:8], POINTS_REELS_CM[0:8], id_cam=1)
        mon_graph.matriceConfig(terrain_manager.points[8:16], POINTS_REELS_CM[8:16], id_cam=2)
        is_calibrated = True
        print("Succès : Les DEUX matrices calibrées instantanément depuis le JSON !")
    except Exception as e:
        print(f"Erreur lors de la calibration initiale : {e}")


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
        packet_id, frame_id = struct.unpack('II', packet[:headerSize])
        payload = packet[headerSize:]

        if frame_id != current_frame_id:
            if current_frame_id != -1 and current_frame_id + 1 == frame_id:
                # Reconstruct the full frame
                full_data = b''.join([data_buffer[i] for i in sorted(data_buffer)])
                frame_data = full_data[messageHeader:]
                frame_buffer = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(frame_buffer, 1)
                
                if frame is not None:
                    
                    # 1. Gestion de la Calibration (Clics manuels)
                    if len(terrain_manager.points) < 16:
                        cv2.putText(frame, f"Calibration: {len(terrain_manager.points)}/16", 
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        is_calibrated = False
                        
                    # Si on vient d'atteindre le 16ème clic
                    elif not is_calibrated:
                        try:
                            # Séparation des caméras ici aussi
                            mon_graph.matriceConfig(terrain_manager.points[0:8], POINTS_REELS_CM[0:8], id_cam=1)
                            mon_graph.matriceConfig(terrain_manager.points[8:16], POINTS_REELS_CM[8:16], id_cam=2)
                            is_calibrated = True
                            print("Succès : Les DEUX matrices calculées après les clics !")
                        except Exception as e:
                            print(f"Erreur de matrice : {e}")

                    # Tracking et Dessin Vidéo
                    ball_info = ball_tracker.get_position(frame)
                    frame = ball_tracker.draw_ball(frame, ball_info)

                    robot_info = robot_tracker.getposition(frame)
                    frame = robot_tracker.drawRobot(frame,robot_info)

                    frame = terrain_manager.draw_zones(frame)

                    coord_cm = None
                    coord_robot_cm = None #par default rien pour la balle et robot

                    if robot_info:
                        pos_robot=robot_info["center"]

                        if is_calibrated:
                            if terrain_manager.is_in_zone(pos_robot, 0):
                                coord_robot_cm = mon_graph.convertir_pixel_to_graph(pos_robot[0], pos_robot[1], cam_id=1)
                            
                           
                            elif terrain_manager.is_in_zone(pos_robot, 1):
                                coord_robot_cm = mon_graph.convertir_pixel_to_graph(pos_robot[0], pos_robot[1], cam_id=2)

                    
                    if ball_info:
                        pos = ball_info["center"]
                        
                        if is_calibrated:
                            # --- Test Zone 1 ---
                            if terrain_manager.is_in_zone(pos, 0):
                                coord_cm = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=1)
                                cv2.putText(frame, "BALLE ZONE 1", (50, 50), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                            
                            # --- Test Zone 2 ---
                            elif terrain_manager.is_in_zone(pos, 1):
                                coord_cm = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=2)
                                cv2.putText(frame, "BALLE ZONE 2", (50, pos[1] - 50), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                            
                            # --- Hors zone ---
                            else:
                                cv2.putText(frame, "BALLE HORS ZONE", (50, 50), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                            # --- Affichage des centimètres ---
                            if coord_cm is not None:
                                texte_cm = f"{coord_cm.x:.1f}cm, {coord_cm.y:.1f}cm"
                                cv2.putText(frame, texte_cm, (pos[0] - 20, pos[1] - 20), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                

                            if coord_cm is not None:
                                if mon_graph.is_but(coord_cm):
                            
                                    cv2.putText(frame, "!!! BUT !!!", (200, 200), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)
                                    print(" La balle est dans la cage !")
                        
               
                    carte_radar = mon_graph.afficher_minimap(coord_balle_cm=coord_cm, coord_robot_cm=coord_robot_cm)
                    cv2.imshow("Radar Terrain Physique (cm)", carte_radar)
                        
                    
                    cv2.imshow(window_name, frame)
                    
                    ch = chr(cv2.waitKey(1) & 0xFF)
                    if ch == 'q' or ch == 'Q': 
                        break
            
            # Reset buffer for new frame
            data_buffer = {}
            current_frame_id = frame_id

        data_buffer[packet_id] = payload
        
    except socket.error:
        continue

sock.close()
cv2.destroyAllWindows()