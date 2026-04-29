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
        self.point=[]
    
    
    def add_point(self,p):
        if 0<= p.x <= self.width and 0<= p.y <= self.length :
            self.point.append(p)
            return True
        else:
            print("le point hors du terrain")
            return False




    

    
        