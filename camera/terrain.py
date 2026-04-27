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

    
    def draw_zones(self, frame):
        """Dessine les polygones sur l'image si assez de points sont présents."""
        for i in range(self.num_zones):
    
            start_idx = i * 8
            end_idx = start_idx + 8
        
        
        if len(self.points) >= end_idx:
            # On récupère les 8 points et on les transforme en format NumPy
            pts = np.array(self.points[start_idx:end_idx], np.int32)
            
            # Couleur : Bleu pour Zone 1, Jaune pour Zone 2
            color = (255, 0, 0) if i == 0 else (0, 255, 255)
            
            # Dessine le polygone à 8 côtés
            cv2.polylines(frame, [pts], True, color, 2)
            
            # Affiche le nom de la zone au niveau du premier point cliqué
            cv2.putText(frame, f"Zone {i+1}", tuple(self.points[start_idx]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return frame