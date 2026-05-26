import math
import socket

CENTRE_CAGE_X = 150
CENTRE_CAGE_Y = 390
DISTANCE_RECULE_CM = 30
TOLERANCE_DST = 15

class TrajectoryLogic:
    def __init__(self, ip_robot, port_robot=9999):
        self.ip_robot = ip_robot
        self.port_robot = port_robot
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.textes_ordres = {0: "AVANCE", 1: "DROITE", 2: "GAUCHE", 3: "STOP"}
        
        # Paramètres terrain
        self.centre_cage_x = CENTRE_CAGE_X
        self.centre_cage_y = CENTRE_CAGE_Y
        
        # Distance derrière la balle pour s'aligner
        self.distance_recul = DISTANCE_RECULE_CM
        
        # Tolérance de distance au point de tir
        self.tolerance_distance = TOLERANCE_DST

        # Mémoire de mouvement pour la logique d'hystérésis
        self.en_mouvement = False

    def calculer_ordre(self, coord_robot_cm, coord_balle_cm):
        # MODIFIÉ : On a supprimé robot_info des paramètres et des vérifications
        if not coord_robot_cm or not coord_balle_cm:
            return 3, "PERTE CIBLE", None 
        
        # --- 1. CALCUL DU POINT DE TIR IDÉAL ---
        vect_x = coord_balle_cm.x - self.centre_cage_x
        vect_y = coord_balle_cm.y - self.centre_cage_y
        angle_vecteur = math.atan2(vect_y, vect_x)
        
        point_tir_x = coord_balle_cm.x + (math.cos(angle_vecteur) * self.distance_recul)
        point_tir_y = coord_balle_cm.y + (math.sin(angle_vecteur) * self.distance_recul)

        # --- 2. CHOIX DE LA CIBLE (ALIGNEMENT OU FRAPPE) ---
        dist_robot_pt_tir = math.hypot(point_tir_x - coord_robot_cm.x, point_tir_y - coord_robot_cm.y)
        
        if dist_robot_pt_tir > self.tolerance_distance:
            # Trop loin, on vise le point derrière la balle pour la contourner
            cible_x = point_tir_x
            cible_y = point_tir_y
            phase = "ALIGNEMENT"
        else:
            # En position, on fonce sur la balle pour marquer
            cible_x = coord_balle_cm.x
            cible_y = coord_balle_cm.y
            phase = "!!! FRAPPE !!!"
        
        # --- 3. PILOTAGE VERS LA CIBLE ---
        dx = cible_x - coord_robot_cm.x
        dy = cible_y - coord_robot_cm.y
        angle_cible = math.degrees(math.atan2(dy, dx))

        # MODIFIÉ : L'IA lit directement l'angle physique unifié stocké dans le Graph !
        angle_robot = coord_robot_cm.angle 
        
        diff_angle = (angle_cible - angle_robot + 180) % 360 - 180

        # AJUSTÉ : Marges pour favoriser les lignes droites (45° en roulant, 20° au pivot)
        marge_erreur = 45 if self.en_mouvement else 20

        if diff_angle > marge_erreur:
            ordre = 2 # PIVOTE GAUCHE
            self.en_mouvement = False
        elif diff_angle < -marge_erreur:
            ordre = 1 # PIVOTE DROITE
            self.en_mouvement = False
        else:
            ordre = 0 # AVANCE
            self.en_mouvement = True

        return ordre, phase, (point_tir_x, point_tir_y)

    def envoyer_ordre(self, ordre):
        """Envoie l'ordre au robot"""
        try:
            self.sock.sendto(str(ordre).encode('utf-8'), (self.ip_robot, self.port_robot))
        except Exception as e:
            print(f"Erreur UDP: {e}")
            
        return self.textes_ordres.get(ordre, "INCONNU")