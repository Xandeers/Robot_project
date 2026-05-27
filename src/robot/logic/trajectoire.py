import math
import socket

CENTRE_CAGE_X = 150
CENTRE_CAGE_Y = 390
DISTANCE_RECULE_CM = 30
TOLERANCE_DST = 15
TOLERANCE_ANGLE_STOP = 20
TOLERANCE_ANGLE_MOVE = 45


class TrajectoryLogic:
    def __init__(self, ip_robot, port_robot=9999):
        self.ip_robot = ip_robot
        self.port_robot = port_robot
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.textes_ordres = {
            0: "AVANCE",
            1: "DROITE",
            2: "GAUCHE",
            3: "STOP"
        }

        self.centre_cage_x = CENTRE_CAGE_X
        self.centre_cage_y = CENTRE_CAGE_Y
        self.distance_recul = DISTANCE_RECULE_CM
        self.tolerance_distance = TOLERANCE_DST

        self.en_mouvement = False

    def calculer_ordre(self, coord_robot_cm, coord_balle_cm):
        if not coord_robot_cm or not coord_balle_cm:
            return 3, "PERTE CIBLE", None

        if not hasattr(coord_robot_cm, "angle"):
            return 3, "ANGLE ROBOT MANQUANT", None

        # Vecteur balle -> cage
        vect_x = self.centre_cage_x - coord_balle_cm.x
        vect_y = self.centre_cage_y - coord_balle_cm.y

        norme = math.hypot(vect_x, vect_y)
        if norme == 0:
            return 3, "BALLE SUR CAGE", None

        dir_x = vect_x / norme
        dir_y = vect_y / norme


        # 1. On crée un vecteur perpendiculaire (on inverse X et Y, et on met un moins)
        perp_x = -dir_y
        perp_y = dir_x
        
        # 2. On place deux points d'esquive à 35 cm sur les côtés de la balle
        ecart = 35
        esquive1_x = coord_balle_cm.x + perp_x * ecart
        esquive1_y = coord_balle_cm.y + perp_y * ecart
        
        esquive2_x = coord_balle_cm.x - perp_x * ecart
        esquive2_y = coord_balle_cm.y - perp_y * ecart

        # --- 3. CHOIX DE LA CIBLE (Esquive, Alignement, ou Frappe) ---
        
        # Le robot est-il "devant" la balle (entre la cage et la balle) ?
        dist_robot_cage = math.hypot(self.centre_cage_x - coord_robot_cm.x, self.centre_cage_y - coord_robot_cm.y)
        dist_balle_cage = math.hypot(self.centre_cage_x - coord_balle_cm.x, self.centre_cage_y - coord_balle_cm.y)
        
        # Point de tir idéal (derrière la balle)
        point_tir_x = coord_balle_cm.x - dir_x * self.distance_recul
        point_tir_y = coord_balle_cm.y - dir_y * self.distance_recul
        
        dist_robot_pt_tir = math.hypot(point_tir_x - coord_robot_cm.x, point_tir_y - coord_robot_cm.y)

        # Si le robot est plus proche de la cage que la balle + marge de 15 cm
        if dist_robot_cage < (dist_balle_cage + 15):
            # Il est du mauvais côté, on vise le point d'esquive le plus proche !
            dist_esquive1 = math.hypot(esquive1_x - coord_robot_cm.x, esquive1_y - coord_robot_cm.y)
            dist_esquive2 = math.hypot(esquive2_x - coord_robot_cm.x, esquive2_y - coord_robot_cm.y)
            
            if dist_esquive1 < dist_esquive2:
                cible_x = esquive1_x
                cible_y = esquive1_y
            else:
                cible_x = esquive2_x
                cible_y = esquive2_y
            phase = "CONTOURNEMENT"
            
        elif dist_robot_pt_tir > self.tolerance_distance:
            # Il est du bon côté de la balle, il s'aligne derrière pour tirer
            cible_x = point_tir_x
            cible_y = point_tir_y
            phase = "ALIGNEMENT"
            
        else:
            # Il est parfaitement en place, on fonce vers le but !
            cible_x = coord_balle_cm.x
            cible_y = coord_balle_cm.y
            phase = "FRAPPE"

        dx = cible_x - coord_robot_cm.x
        dy = cible_y - coord_robot_cm.y

        angle_cible = math.degrees(math.atan2(dy, dx))
        angle_robot = coord_robot_cm.angle

        diff_angle = (angle_cible - angle_robot + 180) % 360 - 180

        marge_erreur = TOLERANCE_ANGLE_MOVE if self.en_mouvement else TOLERANCE_ANGLE_STOP

        if diff_angle > marge_erreur:
            ordre = 2  # GAUCHE
            self.en_mouvement = False
        elif diff_angle < -marge_erreur:
            ordre = 1  # DROITE
            self.en_mouvement = False
        else:
            ordre = 0  # AVANCE
            self.en_mouvement = True

        return ordre, phase, (cible_x, cible_y)

    def envoyer_ordre(self, ordre):
        try:
            self.sock.sendto(str(ordre).encode("utf-8"), (self.ip_robot, self.port_robot))
        except Exception as e:
            print("Erreur UDP: %s" % e)

        return self.textes_ordres.get(ordre, "INCONNU")

