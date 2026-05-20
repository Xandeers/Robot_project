import socket
import cv2
import numpy as np
import struct

from src.camera.terrain import TerrainIMG
from src.camera.Tracker.ball import BallTracker
# Import de ta classe Graph
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
mon_graph = Graph(x_widthCM=301, y_lengthCM=390)
is_calibrated = False

# --- Coordonnées physiques (en centimètres) ---
# À REMPLACER : L'ordre doit correspondre exactement à l'ordre des clics !
POINTS_REELS_CM = [
    # Les 8 points de la Zone 1
    (0, 0), (50, 0), (50, 50), (0, 50), (10, 10), (20, 20), (30, 30), (40, 40), 
    # Les 8 points de la Zone 2
    (100, 0), (150, 0), (150, 50), (100, 50), (110, 10), (120, 20), (130, 30), (140, 40)
]

# Si le fichier JSON existait, TerrainIMG a déjà chargé les 16 points, 
# on peut donc calibrer instantanément :
if len(terrain_manager.points) == 16:
    try:
        mon_graph.matriceConfig(terrain_manager.points, POINTS_REELS_CM, id_cam=1)
        is_calibrated = True
        print("Succès : Matrice calibrée instantanément depuis le JSON !")
    except Exception as e:
        print(f"Erreur lors de la calibration initiale : {e}")

# --- Configuration de la fenêtre vidéo ---
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
                            mon_graph.matriceConfig(terrain_manager.points, POINTS_REELS_CM, id_cam=1)
                            is_calibrated = True
                            print("Succès : Nouvelle matrice calculée après les clics !")
                        except Exception as e:
                            print(f"Erreur de matrice : {e}")

                    # 2. Tracking et Dessin Vidéo
                    ball_info = ball_tracker.get_position(frame)
                    frame = ball_tracker.draw_ball(frame, ball_info)
                    frame = terrain_manager.draw_zones(frame)

                    coord_cm = None  # Par défaut, pas de balle détectée

                    # 3. Logique Balle (Centimètres & Zones)
                    if ball_info:
                        pos = ball_info["center"]
                        
                        if is_calibrated:
                            # Conversion Pixel -> Centimètre
                            coord_cm = mon_graph.convertir_pixel_to_graph(pos[0], pos[1], cam_id=1)
                            texte_cm = f"{coord_cm.x:.1f}cm, {coord_cm.y:.1f}cm"
                            
                            # Affichage sur la vidéo
                            cv2.putText(frame, texte_cm, (pos[0] - 20, pos[1] - 20), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                        # Tests d'appartenance aux zones
                        if terrain_manager.is_in_zone(pos, 0):
                            cv2.putText(frame, "BALLE ZONE 1", (50, 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                        elif terrain_manager.is_in_zone(pos, 1):
                            cv2.putText(frame, "BALLE ZONE 2", (50, 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                        else:
                            cv2.putText(frame, "BALLE HORS ZONE", (50, 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        
                    # 4. Affichage de la Minimap Radar
                    carte_radar = mon_graph.afficher_minimap(coord_cm)
                    cv2.imshow("Radar Terrain Physique (cm)", carte_radar)
                        
                    # 5. Affichage Vidéo Originale
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