import cv2
import numpy as np
import json 
import os
import math # NOUVEAU : Nécessaire pour dessiner la ligne de direction (cos/sin)

class Coordonee:
    def __init__(self, x, y, angle=None):  
        self.x = x
        self.y = y
        self.angle = angle

    def __repr__(self):
        if self.angle is not None:
            return f"({self.x:.1f}, {self.y:.1f}, {self.angle:.1f}°)"
        return f"({self.x:.1f}, {self.y:.1f})"

class Graph:
    def __init__(self, x_widthCM=301, y_lengthCM=390):
        self.width = x_widthCM
        self.length = y_lengthCM
        self.matrice_cam1 = None
        self.matrice_cam2 = None
        self.point = []
        self.cage = None 
    
    def matriceConfig(self, pts_images, pts_graph, id_cam):
        """Prend une liste de points du retour caméra ainsi que leur correspondance dans le graph 
           permet de calculer la matrice qui permet de faire correspondre un point du plan cam choisi"""
        pts_src = np.array(pts_images, dtype=float)
        pts_dst = np.array(pts_graph, dtype=float)

        matrice, _ = cv2.findHomography(pts_src, pts_dst)

        if id_cam == 1: 
            self.matrice_cam1 = matrice
        
        if id_cam == 2:
            self.matrice_cam2 = matrice
        
    def convertir_pixel_to_graph(self, x_pixel, y_pixel, cam_id, angle_cam=None):
        matrix = self.matrice_cam1 if cam_id == 1 else self.matrice_cam2
        
        # 1. Conversion du centre du robot en cm
        point = np.array([[[x_pixel, y_pixel]]], dtype=float)
        point_cm = cv2.perspectiveTransform(point, matrix)
        x_cm = point_cm[0][0][0]
        y_cm = point_cm[0][0][1]
        
        angle_physique = None
        if angle_cam is not None:
            # 2. On crée un point virtuel à 20 pixels devant le nez du robot
            angle_cam_rad = math.radians(angle_cam)
            x_avant_pixel = x_pixel + 20 * math.cos(angle_cam_rad)
            y_avant_pixel = y_pixel + 20 * math.sin(angle_cam_rad)
            
            # 3. On convertit ce point virtuel en cm via la matrice d'homographie
            point_avant = np.array([[[x_avant_pixel, y_avant_pixel]]], dtype=float)
            point_avant_cm = cv2.perspectiveTransform(point_avant, matrix)
            x_avant_cm = point_avant_cm[0][0][0]
            y_avant_cm = point_avant_cm[0][0][1]
            
            # 4. Calcul du véritable angle physique sur le terrain
            dx_cm = x_avant_cm - x_cm
            dy_cm = y_avant_cm - y_cm
            angle_physique = math.degrees(math.atan2(dy_cm, dx_cm))
                
        return Coordonee(x_cm, y_cm, angle=angle_physique)

    def add_point(self, p):
        """Vérifie si le point est dans le terrain et l'ajoute à la liste de pts"""
        if 0 <= p.x <= self.width and 0 <= p.y <= self.length:
            self.point.append(p)
        else:
            print("Le point est hors du terrain")
            
    def is_inside(self, p):
        """Renvoie vrai ou faux si un point est oui ou non dans le terrain"""
        if 0 <= p.x <= self.width and 0 <= p.y <= self.length:
            return True
        else:
            return False
        
    def afficher_minimap(self, coord_balle_cm=None, coord_robot_cm=None, echelle=1.5):
        """
        Crée une carte 2D du terrain (radar) et place la balle et le robot dessus.
        Utilise automatiquement les dimensions définies dans le Graph.
        """
        h = int(self.length * echelle)
        w = int(self.width * echelle)
        minimap = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Contour du terrain blanc
        cv2.rectangle(minimap, (0, 0), (w-1, h-1), (255, 255, 255), 2)
        
        # --- Dessiner la BALLE (Cercle Rouge) ---
        if coord_balle_cm is not None:
            # Récupérer les coordonnées et appliquer l'échelle
            x = int(coord_balle_cm.x * echelle)
            # Inversion de l'axe Y pour l'affichage (OpenCV compte de haut en bas)
            y = h - int(coord_balle_cm.y * echelle) 
            
            # Dessiner la balle (Un cercle rouge plein)
            cv2.circle(minimap, (x, y), 8, (0, 0, 255), -1) 
            
            # Écrire les coordonnées de la balle
            cv2.putText(minimap, f"Balle: ({int(coord_balle_cm.x)}, {int(coord_balle_cm.y)})", 
                        (x + 15, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
        # --- Dessiner le ROBOT (Cercle et ligne de direction) ---
        if coord_robot_cm is not None:
            # Récupérer les coordonnées et appliquer l'échelle
            x_rob = int(coord_robot_cm.x * echelle)
            # Inversion de l'axe Y pour l'affichage
            y_rob = h - int(coord_robot_cm.y * echelle)

            # 1. Dessiner le corps du robot (Cercle Cyan)
            cv2.circle(minimap, (x_rob, y_rob), 12, (255, 255, 0), -1)

            # 2. Dessiner la direction (Le "nez" du robot)
            if coord_robot_cm.angle is not None:
                angle_rad = math.radians(coord_robot_cm.angle)
                longueur_ligne = 25
                
                # Mathématiques pour trouver le bout de la ligne
                # (On fait - sin() car l'axe Y de l'écran OpenCV est inversé vers le bas)
                fin_x = x_rob + int(longueur_ligne * math.cos(angle_rad))
                fin_y = y_rob - int(longueur_ligne * math.sin(angle_rad))
                
                # Tracer une ligne rouge épaisse qui pointe vers l'avant
                cv2.line(minimap, (x_rob, y_rob), (fin_x, fin_y), (0, 0, 255), 3)

            # 3. Écrire les coordonnées ET l'angle
            texte_infos = f"Rob: ({int(coord_robot_cm.x)}, {int(coord_robot_cm.y)})"
            if coord_robot_cm.angle is not None:
                texte_infos += f" | {int(coord_robot_cm.angle)} deg"
                
            cv2.putText(minimap, texte_infos, (x_rob + 15, y_rob - 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
        if self.cage is not None:
            # Convertir les centimètres de la cage en pixels radar
            x1 = int(self.cage["xmin"] * echelle)
            y1 = h - int(self.cage["ymin"] * echelle)
            x2 = int(self.cage["xmax"] * echelle)
            y2 = h - int(self.cage["ymax"] * echelle)
            
            # Dessiner le rectangle
            cv2.rectangle(minimap, (x1, y1), (x2, y2), (0, 165, 255), 3)
            # Écrire "CAGE"
            cv2.putText(minimap, "CAGE", (min(x1, x2), min(y1, y2) - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            
        return minimap

    def set_cage(self, x_min, x_max, y_min, y_max):
        """Définit les dimensions physiques de la cage en centimètres"""
        self.cage = {"xmin": x_min, "xmax": x_max, "ymin": y_min, "ymax": y_max}

    def is_but(self, coord_balle_cm):
        """Vérifie si les coordonnées de la balle sont à l'intérieur de la cage"""
        if not self.cage or not coord_balle_cm:
            return False
        
        dans_x = self.cage["xmin"] <= coord_balle_cm.x <= self.cage["xmax"]
        dans_y = self.cage["ymin"] <= coord_balle_cm.y <= self.cage["ymax"]
        
        return dans_x and dans_y