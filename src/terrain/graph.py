import cv2
import numpy as np
import json 
import os



class Coordonee:
    def __init__(self,x,y, angle=None):  
        self.x=x
        self.y=y
        self.angle=angle


    def __repr__(self):
        if self.angle is not None:
            return f"({self.x:.1f}, {self.y:.1f}, {self.angle:.1f}°)"
        return f"({self.x:.1f}, {self.y:.1f})"




class Graph:
    def __init__(self, x_widthCM=301, y_lengthCM=390):
        self.width=x_widthCM
        self.length=y_lengthCM
        self.matrice_cam1=None
        self.matrice_cam2=None
        self.point = []
        self.cage= None 
    


    def matriceConfig(self,pts_images,pts_graph,id_cam):
        """prend une liste de point du retour camera ainsi que leur correspondance dans le graph 
          permet de calcluler la matrice qui permet de faire correspondre un point du plan cam choisi"""
        
        # pts_image: coordonnéés pixels [(x1,y1), (x2,y2)...]
        # pts_graph: coordonnées cm [(0,0), (301,0)...]
        pts_src=np.array(pts_images, dtype=float)
        pts_dst=np.array(pts_graph, dtype=float)

        matrice,_= cv2.findHomography(pts_src,pts_dst)

        if id_cam == 1 : 
            self.matrice_cam1 = matrice
        
        if id_cam == 2:
            self.matrice_cam2 = matrice
        


    def convertir_pixel_to_graph(self, x_pixel, y_pixel, cam_id, angle_cam=None):
        matrix = self.matrice_cam1 if cam_id == 1 else self.matrice_cam2
        
        point = np.array([[[x_pixel, y_pixel]]], dtype=float)
        point_cm = cv2.perspectiveTransform(point, matrix)
        
       
        angle_physique = None
        if angle_cam is not None:
            if cam_id == 1:
                # Caméra 1 : Inversion de l'axe Y (Pixels vers Graph)
                angle_physique = -angle_cam
            elif cam_id == 2:
                # Caméra 2 (Inversée) : Inversion Y + Demi-tour (180°)
                angle_physique = -angle_cam + 180
                # On force l'angle à rester entre -180 et 180 pour que l'IA ne panique pas
                angle_physique = (angle_physique + 180) % 360 - 180
                
        return Coordonee(point_cm[0][0][0], point_cm[0][0][1], angle=angle_physique)




    
    def add_point(self,p):
        """verifie si le point est dans le terrain et l'ajoute à la liste de pts"""
        if 0<= p.x <= self.width and 0<= p.y <= self.length :
            self.point.append(p)
        else:
            print("le point hors du terrain")
            

    def is_inside(self,p):
        """renvoie vrai ou faux si un point est oui ou non dans le terrain"""
        if 0<= p.x <= self.width and 0<= p.y <= self.length :
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
            
        # --- Dessiner le ROBOT (Triangle Vert) ---
        if coord_robot_cm is not None:
            # Récupérer les coordonnées et appliquer l'échelle
            x_rob = int(coord_robot_cm.x * echelle)
            # Inversion de l'axe Y pour l'affichage
            y_rob = h - int(coord_robot_cm.y * echelle)

            # Définir les sommets d'un triangle pour représenter le robot
            taille = 15
            sommet1 = (x_rob, y_rob - taille)
            sommet2 = (x_rob - taille, y_rob + taille)
            sommet3 = (x_rob + taille, y_rob + taille)
            points_triangle = np.array([sommet1, sommet2, sommet3], np.int32)

            # Dessiner le triangle vert plein
            cv2.drawContours(minimap, [points_triangle], 0, (0, 255, 0), -1)

            # Écrire les coordonnées du robot
            cv2.putText(minimap, f"Robot: ({int(coord_robot_cm.x)}, {int(coord_robot_cm.y)})",
                        (x_rob + 15, y_rob - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
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


    

    

    
        