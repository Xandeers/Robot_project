import cv2
import numpy as np
import json 
import os



class Coordonee:
    def __init__(self,x,y):  
        self.x=x
        self.y=y


    def __repr__(self):
        print(f"({self.x},{self.y})")




class Graph:
    def __init__(self, x_widthCM=301, y_lengthCM=390):
        self.width=x_widthCM
        self.length=y_lengthCM
        self.matrice_cam1=None
        self.matrice_cam2=None
        self.point = []
    


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
        


    def convertir_pixel_to_graph(self, x_pixel, y_pixel, cam_id):
        matrix = self.matrice_cam1 if cam_id == 1 else self.matrice_cam2
        
        point = np.array([[[x_pixel, y_pixel]]], dtype=float)
        point_cm = cv2.perspectiveTransform(point, matrix)
        return Coordonee(point_cm[0][0][0], point_cm[0][0][1])





    
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
        

    def afficher_minimap(self, coord_cm=None, echelle=1.5):
        """
        Crée une carte 2D du terrain (radar) et place la balle dessus.
        Utilise automatiquement les dimensions définies dans le Graph.
        """
        h = int(self.length * echelle)
        w = int(self.width * echelle)
        minimap = np.zeros((h, w, 3), dtype=np.uint8)
        
        # contour du terrain blanc
        cv2.rectangle(minimap, (0, 0), (w-1, h-1), (255, 255, 255), 2)
        
        if coord_cm is not None:
            # Récupérer les coordonnées et appliquer l'échelle
            x = int(coord_cm.x * echelle)
            # Inversion de l'axe Y pour l'affichage (OpenCV compte de haut en bas)
            y = h - int(coord_cm.y * echelle) 
            
            # Dessiner la balle (Un cercle rouge plein)
            cv2.circle(minimap, (x, y), 8, (0, 0, 255), -1) 
            
            # Écrire les coordonnées
            cv2.putText(minimap, f"({int(coord_cm.x)}, {int(coord_cm.y)})", 
                        (x + 15, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
        return minimap




    

    
        