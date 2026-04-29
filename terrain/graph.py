import cv2
import numpy as np
import json 
import os



class Coordonee:
    def __init__(self,x,y):  
        self.x=x
        self.y=y


    def __repr__(self,p):
        print(f"({p.x},{p.y})")




class Graph:
    def __init__(self, x_widthCM=301, y_lengthCM=390):
        self.width=x_widthCM
        self.length=y_lengthCM
        self.matrice_cam1=None
        self.matrice_cam2=None
    


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
        
    




    

    
        