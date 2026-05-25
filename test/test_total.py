import socket
import cv2
import numpy as np
import struct

from src.camera.terrain import TerrainIMG
from src.camera.Tracker.ball import BallTracker
from src.camera.Tracker.robot import RobotTracker
from src.robot.logic.trajectoire import TrajectoryLogic
from src.terrain.graph import Graph 



IP_ROBOT="172.0.0.1"

# --- Configuration Réseau (Réception Vidéo) ---
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
mon_graph = Graph(x_widthCM=301, y_lengthCM=390)
mon_graph.set_cage(x_min=100, x_max=200, y_min=370, y_max=390)

# Envoi vers EV3 
ia_trajectoire = TrajectoryLogic(ip_robot=IP_ROBOT, port_robot=9999) 

is_calibrated = False

# --- Coordonnées physiques (en centimètres) ---
POINTS_REELS_CM = [
    # --- ZONE 1 (Flux Caméra 1) ---
    (0, 195), (150.5, 195), (301, 195), (301, 292.5), 
    (301, 390), (150.5, 390), (0, 390), (0, 292.5),
    # --- ZONE 2 (Flux Caméra 2 - Inversée) ---
    (301, 195), (150.5, 195), (0, 195), (0, 97.5), 
    (0, 0), (150.5, 0), (301, 0), (301, 97.5)
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

# --- Boucle Principale ---
while True:
    try:
        packet, addr = sock.recvfrom(MaximumPacketSize)
        packet_id, frame_id = struct.unpack('II', packet[:headerSize])
        payload = packet[headerSize:]

        if frame_id != current_frame_id:
            if current_frame_id != -1 and current_frame_id + 1 == frame_id:
                full_data = b''.join([data_buffer[i] for i in sorted(data_buffer)])
                frame_data = full_data[messageHeader:]
                frame_buffer = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(frame_buffer, 1)
                
                if frame is not None:
                    # 1. Calibration
                    if len(terrain_manager.points) < 16:
                        cv2.putText(frame, f"Calibration: {len(terrain_manager.points)}/16", 
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        is_calibrated = False
                    elif not is_calibrated:
                        try:
                            mon_graph.matriceConfig(terrain_manager.points[0:8], POINTS_REELS_CM[0:8], id_cam=1)
                            mon_graph.matriceConfig(terrain_manager.points[8:16], POINTS_REELS_CM[8:16], id_cam=2)
                            is_calibrated = True
                            print("Succès : Les DEUX matrices calculées après les clics !")
                        except Exception as e:
                            print(f"Erreur de matrice : {e}")

                    # 2. Tracking
                    ball_info = ball_tracker.get_position(frame)
                    frame = ball_tracker.draw_ball(frame, ball_info)

                    robot_info = robot_tracker.getposition(frame)
                    frame = robot_tracker.drawRobot(frame, robot_info)

                    frame = terrain_manager.draw_zones(frame)

                    coord_cm = None
                    coord_robot_cm = None

                    # Calcul Robot (cm)
                    if robot_info and is_calibrated:
                        pos_robot = robot_info["center"]
                        if terrain_manager.is_in_zone(pos_robot, 0):
                            coord_robot_cm = mon_graph.convertir_pixel_to_graph(pos_robot[0], pos_robot[1], cam_id=1)
                        elif terrain_manager.is_in_zone(pos_robot, 1):
                            coord_robot_cm = mon_graph.convertir_pixel_to_graph(pos_robot[0], pos_robot[1], cam_id=2)

                    # Calcul Balle (cm)
                    if ball_info and is_calibrated:
                        pos = ball_info["center"]
                        if terrain_manager.is_in_zone(pos, 0):
                            coord_cm = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=1)
                        elif terrain_manager.is_in_zone(pos, 1):
                            coord_cm = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=2)

                        # Affichage But
                        if coord_cm is not None:
                            if mon_graph.is_but(coord_cm):
                                cv2.putText(frame, "!!! BUT !!!", (200, 200), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)

                    # --- 3. INTELLIGENCE ARTIFICIELLE & PILOTAGE EV3 ---
                    if coord_cm is not None and coord_robot_cm is not None:
                        # Le cerveau calcule la meilleure action
                        ordre, phase, pt_tir = ia_trajectoire.calculer_ordre(robot_info, coord_robot_cm, coord_cm)
                        
                        # Le PC envoie directement l'ordre au robot (remplace ton fichier test)
                        nom_ordre = ia_trajectoire.envoyer_ordre(ordre)
                        
                        # Affichage sur l'écran
                        cv2.putText(frame, f"Phase: {phase}", (10, 80), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                        cv2.putText(frame, f"Action: {nom_ordre}", (10, 110), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        
                    # 4. Affichage Radar & Vidéo
                    carte_radar = mon_graph.afficher_minimap(coord_balle_cm=coord_cm, coord_robot_cm=coord_robot_cm)
                    cv2.imshow("Radar Terrain Physique (cm)", carte_radar)
                    cv2.imshow(window_name, frame)
                    
                    ch = chr(cv2.waitKey(1) & 0xFF)
                    if ch == 'q' or ch == 'Q': 
                        break
            
            data_buffer = {}
            current_frame_id = frame_id

        data_buffer[packet_id] = payload
        
    except socket.error:
        continue

# --- SÉCURITÉ : ARRÊT DU ROBOT À LA FERMETURE ---
print("Fermeture... Envoi de l'ordre STOP au robot.")
ia_trajectoire.envoyer_ordre(3)

sock.close()
cv2.destroyAllWindows()