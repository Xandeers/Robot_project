import socket
import cv2
import numpy as np
import struct
import math

# Tes imports locaux
from camera.terrain import TerrainIMG
from camera.Tracker.ball import BallTracker
from src.terrain.graph import Graph, Coordonee 

# =====================================================================
# 1. CONFIGURATION RÉSEAU ET TERRAIN
# =====================================================================
# --- Vidéo (Réception) ---
ip_video = ""  
port_video = 8080
MaximumPacketSize = 1400

# --- Robot EV3 (Envoi) ---
IP_ROBOT = "192.168.1.50"  # 🔴 REMPLACE PAR L'IP DE TON EV3
PORT_ROBOT = 9999
sock_robot = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Socket d'envoi UDP

# --- Terrain ---
LARGEUR_TERRAIN = 301.0
LONGUEUR_TERRAIN = 390.0
pos_but = Coordonee(LARGEUR_TERRAIN / 2.0, 20.0) 

# =====================================================================
# 2. INITIALISATION DES OUTILS
# =====================================================================
terrain_manager = TerrainIMG(num_zones=2, points_per_zone=8)
ball_tracker = BallTracker()
graph = Graph(x_widthCM=LARGEUR_TERRAIN, y_lengthCM=LONGUEUR_TERRAIN)
matrice_calibre = False

sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_video.bind((ip_video, port_video))

print("📡 Écoute de la caméra en cours...")
print(f"🚀 Prêt à bombarder le robot sur {IP_ROBOT}:{PORT_ROBOT}...")

window_name = "Cerveau PC - Vision & Contrôle"
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, terrain_manager.mouse_callback)

# =====================================================================
# 3. FONCTIONS D'INTELLIGENCE
# =====================================================================
def trouver_robot_aruco(frame):
    """Trouve le marqueur ArUco et déduit le centre et l'angle du robot"""
    try:
        dictionnaire = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parametres = cv2.aruco.DetectorParameters()
        detecteur = cv2.aruco.ArucoDetector(dictionnaire, parametres)
        coins, ids, _ = detecteur.detectMarkers(frame)
    except AttributeError:
        # Pour les anciennes versions d'OpenCV
        dictionnaire = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        parametres = cv2.aruco.DetectorParameters_create()
        coins, ids, _ = cv2.aruco.detectMarkers(frame, dictionnaire, parameters=parametres)

    if ids is not None:
        c = coins[0][0] 
        centre_x = int(np.mean(c[:, 0]))
        centre_y = int(np.mean(c[:, 1]))
        
        # Angle vers l'avant (du coin bas-gauche vers haut-gauche pour un ArUco standard)
        dx = c[1][0] - c[0][0]
        dy = c[1][1] - c[0][1]
        angle_rad = math.atan2(dy, dx)
        
        cv2.aruco.drawDetectedMarkers(frame, coins, ids)
        # On dessine une flèche verte pour voir où le PC pense que le robot regarde
        cv2.arrowedLine(frame, (centre_x, centre_y), (int(centre_x + dx), int(centre_y + dy)), (0, 255, 0), 2)
        
        return {"center": (centre_x, centre_y), "angle_rad": angle_rad}
    return None

def calcul_action_vectorielle(pos_robot, pos_balle, pos_but, angle_robot_rad):
    v_but_x = pos_but.x - pos_balle.x
    v_but_y = pos_but.y - pos_balle.y
    dist_balle_but = np.sqrt(v_but_x**2 + v_but_y**2)
    
    if dist_balle_but < 0.1: return 4 
        
    u_but_x = v_but_x / dist_balle_but
    u_but_y = v_but_y / dist_balle_but
    
    cible_x = pos_balle.x - (u_but_x * 20.0)
    cible_y = pos_balle.y - (u_but_y * 20.0)
    
    dx = cible_x - pos_robot.x
    dy = cible_y - pos_robot.y
    dist_cible = np.sqrt(dx**2 + dy**2)
    
    if dist_cible < 15.0:
        dx = pos_balle.x - pos_robot.x
        dy = pos_balle.y - pos_robot.y
        
    angle_ideal = math.atan2(-dy, dx)
    erreur_angle = angle_ideal - angle_robot_rad
    erreur_angle = (erreur_angle + math.pi) % (2 * math.pi) - math.pi
    
    SEUIL = math.radians(12) 
    if erreur_angle > SEUIL: return 2
    elif erreur_angle < -SEUIL: return 3
    else: return 0

def envoyer_ordre_ev3(action):
    """Tire un paquet UDP au robot"""
    try:
        message = f"{action}\n".encode('utf-8')
        sock_robot.sendto(message, (IP_ROBOT, PORT_ROBOT))
    except:
        pass

# =====================================================================
# 4. BOUCLE VIDÉO ET CONTRÔLE
# =====================================================================
data_buffer = {}
current_frame_id = -1
messageHeader = 4
headerSize = 8

while True:
    try:
        packet, addr = sock_video.recvfrom(MaximumPacketSize)
        packet_id, frame_id = struct.unpack('II', packet[:headerSize])
        payload = packet[headerSize:]

        if frame_id != current_frame_id:
            if current_frame_id != -1 and current_frame_id + 1 == frame_id:
                full_data = b''.join([data_buffer[i] for i in sorted(data_buffer)])
                frame_buffer = np.frombuffer(full_data[messageHeader:], dtype=np.uint8)
                frame = cv2.imdecode(frame_buffer, 1)
                
                if frame is not None:
                    # -- 1. HOMOGRAPHIE --
                    if len(terrain_manager.points) == 16 and not matrice_calibre:
                        pts_pixels = terrain_manager.points[0:4]
                        pts_cm = [(0, 0), (LARGEUR_TERRAIN, 0), (LARGEUR_TERRAIN, LONGUEUR_TERRAIN), (0, LONGUEUR_TERRAIN)]
                        graph.matriceConfig(pts_pixels, pts_cm, id_cam=1)
                        matrice_calibre = True
                        print("✅ Calibrage Terrain OK !")

                    if len(terrain_manager.points) < 16:
                        cv2.putText(frame, f"Calibration: {len(terrain_manager.points)}/16", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                    # -- 2. TRACKING --
                    ball_info = ball_tracker.get_position(frame)
                    robot_info = trouver_robot_aruco(frame)
                    
                    frame = ball_tracker.draw_ball(frame, ball_info)
                    frame = terrain_manager.draw_zones(frame)

                    # -- 3. DÉCISION ET TIR RÉSEAU --
                    if ball_info and robot_info and matrice_calibre:
                        pos_ball_px = ball_info["center"]
                        pos_robot_px = robot_info["center"]
                        
                        cam_active = 1
                        if terrain_manager.is_in_zone(pos_ball_px, 1): cam_active = 2

                        pos_robot_cm = graph.convertir_pixel_to_graph(pos_robot_px[0], pos_robot_px[1], cam_id=cam_active)
                        pos_balle_cm = graph.convertir_pixel_to_graph(pos_ball_px[0], pos_ball_px[1], cam_id=cam_active)
                        
                        action = calcul_action_vectorielle(pos_robot_cm, pos_balle_cm, pos_but, robot_info["angle_rad"])
                        envoyer_ordre_ev3(action)
                    else:
                        envoyer_ordre_ev3(4) # Stop sécurité si on perd la vue

                    cv2.imshow(window_name, frame)
                    if chr(cv2.waitKey(1) & 0xFF).lower() == 'q': break
            
            data_buffer = {}
            current_frame_id = frame_id

        data_buffer[packet_id] = payload
    except socket.error:
        continue

sock_video.close()
cv2.destroyAllWindows()