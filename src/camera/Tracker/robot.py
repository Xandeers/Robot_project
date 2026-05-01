import cv2
import numpy as np 



class RobotTracker :
    def __init__(self):
    
        self.lower_green = np.array([35, 100, 50])   
        self.upper_green = np.array([85, 255, 255])
