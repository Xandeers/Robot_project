import math
import socket

CENTRE_CAGE_X = 150
CENTRE_CAGE_Y = 390
DISTANCE_RECULE_CM = 30
TOLERANCE_DST = 15
TOLERANCE_ANGLE_STOP = 20
TOLERANCE_ANGLE_MOVE = 45
CONE_VISION=70
DIST_DANGER=15


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

    # NOUVEAU : Ajout des listes d'obstacles et du statut de la balle
    def calculer_ordre(self, coord_robot_cm, coord_balle_cm, coord_enemies_cm=None, coord_allies_cm=None, balle_en_jeu=True, balle_au_but=False):
        if coord_enemies_cm is None: coord_enemies_cm = []
        if coord_allies_cm is None: coord_allies_cm = []

        if not coord_robot_cm:
            return 3, "PERTE ROBOT", None

        if not hasattr(coord_robot_cm, "angle"):
            return 3, "ANGLE ROBOT MANQUANT", None

        # ====================================================
        # 1. GESTION DU BUT (RETOUR AU POINT D'ENGAGEMENT)
        # ====================================================
        if balle_au_but:
            cible_x = 150
            cible_y = 50  # Coordonnées de ta zone de départ (à ajuster si besoin)
            phase = "RETOUR ENGAGEMENT"

        # ====================================================
        # 2. GESTION BALLE HORS-TERRAIN (REPLI)
        # ====================================================
        elif not balle_en_jeu or not coord_balle_cm:
            # Si la balle est sortie, on va au milieu de notre camp
            cible_x = 150
            cible_y = 100
            phase = "REPLI (ATTENTE)"

        else:
            # ====================================================
            # 3. DÉTECTION COLLISION (CÔNE AVANT UNIQUEMENT)
            # ====================================================
            dangers = coord_enemies_cm + coord_allies_cm
            danger_distance = DIST_DANGER  # Zone critique (cm)
            closest_danger = None
            min_dist = float('inf')

            for danger_data in dangers:
                d_coord = danger_data["coord"]
                dist_danger = math.hypot(d_coord.x - coord_robot_cm.x, d_coord.y - coord_robot_cm.y)
                
                # S'il est assez près
                if dist_danger < danger_distance:
                    dx_obs = d_coord.x - coord_robot_cm.x
                    dy_obs = d_coord.y - coord_robot_cm.y
                    angle_obs = math.degrees(math.atan2(dy_obs, dx_obs))
                    
                    diff_angle_obs = (angle_obs - coord_robot_cm.angle + 180) % 360 - 180
                    
                    # Cône de vision : est-ce qu'il est DEVANT nous (+/- 70°) ?
                    if abs(diff_angle_obs) < CONE_VISION:
                        if dist_danger < min_dist:
                            min_dist = dist_danger
                            closest_danger = d_coord

            if closest_danger is not None:
                # ---> DANGER DEVANT : Esquive Latérale (Glissement)
                phase = "ESQUIVE COLLISION"
                
                fuite_x = coord_robot_cm.x - closest_danger.x
                fuite_y = coord_robot_cm.y - closest_danger.y
                norme = math.hypot(fuite_x, fuite_y)

                if norme != 0:
                    fuite_x /= norme
                    fuite_y /= norme

                # Vecteur perpendiculaire pour le décalage sur le côté
                gliss_x = -fuite_y
                gliss_y = fuite_x

                cible_x = coord_robot_cm.x + (fuite_x * 10) + (gliss_x * 35)
                cible_y = coord_robot_cm.y + (fuite_y * 10) + (gliss_y * 35)

            else:
                # ====================================================
                # 3. LOGIQUE FOOTBALL (TON CODE ORIGINAL INTACT)
                # ====================================================
                vect_x = self.centre_cage_x - coord_balle_cm.x
                vect_y = self.centre_cage_y - coord_balle_cm.y

                norme = math.hypot(vect_x, vect_y)
                if norme == 0:
                    return 3, "BALLE SUR CAGE", None

                dir_x = vect_x / norme
                dir_y = vect_y / norme

                # 1. Vecteur perpendiculaire pour les points d'esquive balle
                perp_x = -dir_y
                perp_y = dir_x
                
                # 2. Points d'esquive de la balle à 35 cm
                ecart = 35
                esquive1_x = coord_balle_cm.x + perp_x * ecart
                esquive1_y = coord_balle_cm.y + perp_y * ecart
                
                esquive2_x = coord_balle_cm.x - perp_x * ecart
                esquive2_y = coord_balle_cm.y - perp_y * ecart
                
                dist_robot_cage = math.hypot(self.centre_cage_x - coord_robot_cm.x, self.centre_cage_y - coord_robot_cm.y)
                dist_balle_cage = math.hypot(self.centre_cage_x - coord_balle_cm.x, self.centre_cage_y - coord_balle_cm.y)
                
                # Point de tir idéal
                point_tir_x = coord_balle_cm.x - dir_x * self.distance_recul
                point_tir_y = coord_balle_cm.y - dir_y * self.distance_recul
                
                dist_robot_pt_tir = math.hypot(point_tir_x - coord_robot_cm.x, point_tir_y - coord_robot_cm.y)

                if dist_robot_cage < (dist_balle_cage + 15):
                    # Mauvais côté -> Contournement de la balle
                    dist_esquive1 = math.hypot(esquive1_x - coord_robot_cm.x, esquive1_y - coord_robot_cm.y)
                    dist_esquive2 = math.hypot(esquive2_x - coord_robot_cm.x, esquive2_y - coord_robot_cm.y)
                    
                    if dist_esquive1 < dist_esquive2:
                        cible_x = esquive1_x
                        cible_y = esquive1_y
                    else:
                        cible_x = esquive2_x
                        cible_y = esquive2_y
                    phase = "CONTOURNEMENT BALLE"
                    
                elif dist_robot_pt_tir > self.tolerance_distance:
                    # Bon côté -> Alignement
                    cible_x = point_tir_x
                    cible_y = point_tir_y
                    phase = "ALIGNEMENT"
                    
                else:
                    # En place -> Frappe
                    cible_x = coord_balle_cm.x
                    cible_y = coord_balle_cm.y
                    phase = "FRAPPE"

        # ====================================================
        # PILOTAGE FINAL MOTEUR (Commun à toutes les phases)
        # ====================================================
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