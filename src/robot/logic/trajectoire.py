import math
import socket

CENTRE_CAGE_X= 150
CENTRE_CAGE_Y= 390
DISTANCE_RECULE_CM =30
TOLERANCE_DST=15
TOLERANCE_ANGL=15



class TrajectoryLogic:
    def __init__(self, ip_robot, port_robot=9999):
        self.ip_robot = ip_robot
        self.port_robot = port_robot
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.textes_ordres = {0: "AVANCE", 1: "DROITE", 2: "GAUCHE", 3: "STOP"}
        
        # param terrain
        self.centre_cage_x = CENTRE_CAGE_X
        self.centre_cage_y = CENTRE_CAGE_Y
        
        # distancce  deriere la balle 
        self.distance_recul = DISTANCE_RECULE_CM
        
        # Tolérance 
        self.tolerance_distance = TOLERANCE_DST

    
    def calculer_ordre(self, robot_info, coord_robot_cm, coord_balle_cm):
        if not coord_robot_cm or not coord_balle_cm or not robot_info:
            return 3, "PERTE CIBLE", None 
        
        # calcul pts de tir
        # Vect de la cage et vers balle
        vect_x = coord_balle_cm.x - self.centre_cage_x
        vect_y = coord_balle_cm.y - self.centre_cage_y
        
        # Angle
        angle_vecteur = math.atan2(vect_y, vect_x)
        
        # Crea du pts de tir dans alignement, derrière la balle
        point_tir_x = coord_balle_cm.x + (math.cos(angle_vecteur) * self.distance_recul)
        point_tir_y = coord_balle_cm.y + (math.sin(angle_vecteur) * self.distance_recul)

        
        # choix cible 
        # dist robot et pts de tir
        dist_robot_pt_tir = math.hypot(point_tir_x - coord_robot_cm.x, point_tir_y - coord_robot_cm.y)
        
        
        if dist_robot_pt_tir > self.tolerance_distance:
            #trop loin dcp vise pts de tir
            cible_x = point_tir_x
            cible_y = point_tir_y
            phase = "ALIGNEMENT"
        else:
            # ok alors on fappe 
            cible_x = coord_balle_cm.x
            cible_y = coord_balle_cm.y
            phase = "!!! FRAPPE !!!"
        
        # pilotage vers cible 
        dx = cible_x - coord_robot_cm.x
        dy = cible_y - coord_robot_cm.y
        angle_cible = math.degrees(math.atan2(dy, dx))

        angle_robot = robot_info["angle"]
        diff_angle = (angle_cible - angle_robot + 180) % 360 - 180

        marge_erreur_angle = TOLERANCE_ANGL

        if diff_angle > marge_erreur_angle:
            ordre = 1 # PIVOTE DROITE
        elif diff_angle < -marge_erreur_angle:
            ordre = 2 # PIVOTE GAUCHE 
        else:
            ordre = 0 # AVANCE

        return ordre, phase, (point_tir_x, point_tir_y)
    

    def envoyer_ordre(self, ordre):
        """Envoie l'ordre au robot"""
        try:
            self.sock.sendto(str(ordre).encode('utf-8'), (self.ip_robot, self.port_robot))
        except Exception as e:
            print(f"Erreur UDP: {e}")
            
        return self.textes_ordres.get(ordre, "INCONNU")