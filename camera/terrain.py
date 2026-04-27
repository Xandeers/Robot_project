import cv2
import numpy as np

class Terrain:
    
    def __init__(self, num_zones=2, points_per_zone=8):
        self.points = []
        self.max_points = num_zones * points_per_zone
        self.num_zones = num_zones


    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.points) < self.max_points:
                self.points.append((x, y))
                print(f"Point {len(self.points)} enregistré : ({x}, {y})")