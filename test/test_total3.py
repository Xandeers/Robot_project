import socket
import cv2
import numpy as np
import struct
import threading

from src.camera.terrain import TerrainIMG
from src.camera.Tracker.ball import BallTracker
from src.camera.Tracker.robot import RobotTracker
from src.robot.logic.trajectoire import TrajectoryLogic
from src.terrain.graph import Graph, Coordonee


from src.camera.Tracker.enemy import EnemyTracker  # Ton nouveau tracker d'essaim
from supervison.server import lancer_dashbord, envoye # L'interface Web

IP_ROBOT="172.20.10.3"

# --- Lancement du Serveur Web (Dashboard) ---
print("Démarrage de l'interface de supervision en arrière-plan...")
# On place le serveur dans un thread pour qu'il ne bloque pas la caméra
thread_serveur = threading.Thread(target=lancer_dashbord, daemon=True)
thread_serveur.start()

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

# NOUVEAU : Initialisation de l'EnemyTracker (ID 2 est un allié par exemple)
enemy_tracker = EnemyTracker(main_id=1, ally_ids=[2])

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

# --- Variables pour le filtre et l'Hystérésis ---
zone_active_robot = 0
robot_filtre_x = None
robot_filtre_y = None
robot_filtre_angle = None
ALPHA = 0.98  # Force du lissage


# ==========================================
# BOUCLE PRINCIPALE DE JEU
# ==========================================
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
                            print("Succès : Les DEUX matrices calculées !")
                        except Exception as e:
                            print(f"Erreur de matrice : {e}")

                    # ==========================================
                    # 2. TRACKING VISUEL (Pixels)
                    # ==========================================
                    ball_info = ball_tracker.get_position(frame)
                    frame = ball_tracker.draw_ball(frame, ball_info)

                    robot_info = robot_tracker.getposition(frame)
                    frame = robot_tracker.drawRobot(frame, robot_info)
                    
                    # NOUVEAU : Tracking des Ennemis & Alliés
                    allies_info, enemies_info = enemy_tracker.get_positions(frame)
                    frame = enemy_tracker.draw_entities(frame, allies_info, enemies_info)

                    frame = terrain_manager.draw_zones(frame)

                    # Initialisation des variables CM
                    coord_cm = None          # Balle
                    coord_robot_cm = None    # Idefix
                    coord_enemies_cm = []    # Ennemis
                    coord_allies_cm = []     # Alliés

                    # ==========================================
                    # 3. CONVERSION MATRICIELLE (Pixels -> Centimètres)
                    # ==========================================
                    if is_calibrated:
                        # --- IDEFIX (Hystérésis & Filtre) ---
                        if robot_info:
                            pos_robot = robot_info["center"]
                            angle_camera = robot_info["angle"] 
                            
                            in_zone_0 = terrain_manager.is_in_zone(pos_robot, 0)
                            in_zone_1 = terrain_manager.is_in_zone(pos_robot, 1)
                            
                            if in_zone_0 and in_zone_1:
                                pass 
                            elif in_zone_0:
                                zone_active_robot = 0
                            elif in_zone_1:
                                zone_active_robot = 1
                                
                            coord_brute = None
                            if zone_active_robot == 0:
                                coord_brute = mon_graph.convertir_pixel_to_graph(pos_robot[0], pos_robot[1], cam_id=1, angle_cam=angle_camera)
                            elif zone_active_robot == 1:
                                coord_brute = mon_graph.convertir_pixel_to_graph(pos_robot[0], pos_robot[1], cam_id=2, angle_cam=angle_camera)

                            if coord_brute is not None:
                                if robot_filtre_x is None:
                                    robot_filtre_x = coord_brute.x
                                    robot_filtre_y = coord_brute.y
                                    robot_filtre_angle = coord_brute.angle
                                else:
                                    robot_filtre_x = (1 - ALPHA) * robot_filtre_x + ALPHA * coord_brute.x
                                    robot_filtre_y = (1 - ALPHA) * robot_filtre_y + ALPHA * coord_brute.y
                                    if coord_brute.angle is not None and robot_filtre_angle is not None:
                                        diff_angle = (coord_brute.angle - robot_filtre_angle + 180) % 360 - 180
                                        robot_filtre_angle = robot_filtre_angle + ALPHA * diff_angle
                                        
                                coord_robot_cm = Coordonee(robot_filtre_x, robot_filtre_y, angle=robot_filtre_angle)

                        # --- BALLE ---
                        if ball_info:
                            pos = ball_info["center"]
                            if terrain_manager.is_in_zone(pos, 0):
                                coord_cm = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=1)
                            elif terrain_manager.is_in_zone(pos, 1):
                                coord_cm = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=2)

                        # --- NOUVEAU : ENNEMIS ET ALLIÉS ---
                        for en in enemies_info:
                            pos = en["center"]
                            if terrain_manager.is_in_zone(pos, 0):
                                c = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=1)
                                if c: coord_enemies_cm.append({"id": en["id"], "coord": c})
                            elif terrain_manager.is_in_zone(pos, 1):
                                c = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=2)
                                if c: coord_enemies_cm.append({"id": en["id"], "coord": c})
                                
                        for al in allies_info:
                            pos = al["center"]
                            if terrain_manager.is_in_zone(pos, 0):
                                c = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=1)
                                if c: coord_allies_cm.append({"id": al["id"], "coord": c})
                            elif terrain_manager.is_in_zone(pos, 1):
                                c = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=2)
                                if c: coord_allies_cm.append({"id": al["id"], "coord": c})


                    # ==========================================
                    # 4. ÉTATS DU MATCH ET INTELLIGENCE ARTIFICIELLE
                    # ==========================================
                    balle_en_jeu = False
                    balle_au_but = False
                    
                    if coord_cm is not None:
                        balle_en_jeu = mon_graph.is_inside(coord_cm)
                        balle_au_but = mon_graph.is_but(coord_cm)
                        
                        if balle_au_but:
                            cv2.putText(frame, "!!! BUT !!!", (200, 200), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)

                    ordre = 3
                    phase = "ATTENTE"
                    pt_tir = None

                    if coord_robot_cm is not None:
                        # Appel au nouveau Cerveau
                        ordre, phase, pt_tir = ia_trajectoire.calculer_ordre(
                            coord_robot_cm=coord_robot_cm, 
                            coord_balle_cm=coord_cm, 
                            coord_enemies_cm=coord_enemies_cm, 
                            coord_allies_cm=coord_allies_cm,
                            balle_en_jeu=balle_en_jeu,
                            balle_au_but=balle_au_but
                        )
                        
                        nom_ordre = ia_trajectoire.envoyer_ordre(ordre)
                        
                        cv2.putText(frame, f"Phase: {phase}", (10, 80), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                        cv2.putText(frame, f"Action: {nom_ordre}", (10, 110), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)


                    # ==========================================
                    # 5. SYNCHRONISATION DASHBOARD WEB (SocketIO)
                    # ==========================================
                    # Extraction sécurisée des données pour le web
                    web_rx = coord_robot_cm.x if coord_robot_cm else 0
                    web_ry = coord_robot_cm.y if coord_robot_cm else 0
                    web_ra = coord_robot_cm.angle if (coord_robot_cm and coord_robot_cm.angle) else 0
                    web_bx = coord_cm.x if coord_cm else 0
                    web_by = coord_cm.y if coord_cm else 0
                    web_cx = pt_tir[0] if pt_tir else 0
                    web_cy = pt_tir[1] if pt_tir else 0
                    
                    ennemis_web = [{"id": e["id"], "x": e["coord"].x, "y": e["coord"].y} for e in coord_enemies_cm]
                    allies_web = [{"id": a["id"], "x": a["coord"].x, "y": a["coord"].y} for a in coord_allies_cm]
                    
                    envoye(
                        robot_x=web_rx, robot_y=web_ry, robot_angle=web_ra, 
                        ball_x=web_bx, ball_y=web_by, 
                        phase=phase, ordre=ordre,
                        enemies=ennemis_web, allies=allies_web,
                        cible_x=web_cx, cible_y=web_cy,
                        balle_en_jeu=balle_en_jeu
                    )


                    # ==========================================
                    # 6. AFFICHAGES OPENCV LOCAUX
                    # ==========================================
                    carte_radar = mon_graph.afficher_minimap(
                        coord_balle_cm=coord_cm, 
                        coord_robot_cm=coord_robot_cm,
                        coord_enemies_cm=coord_enemies_cm,
                        coord_allies_cm=coord_allies_cm
                    )
                    
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