import cv2
import numpy as np
import json 
import os

class TerrainIMG:

    def __init__(self, num_zones=2, points_per_zone=8, filename="points_terrain.json"):
        self.points = []
        self.max_points = num_zones * points_per_zone
        self.num_zones = num_zones
        self.filename = filename
        self.load_points()

    def load_points(self):
        """Charge les points depuis le fichier JSON s'il existe."""
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                self.points = json.load(f)
            print(f"Points chargés depuis {self.filename} ({len(self.points)} points)")


    def save_points(self):
        """Enregistre la liste de points dans un fichier JSON."""
        with open(self.filename, 'w') as f:
            json.dump(self.points, f)
        print(f"Points sauvegardés dans {self.filename}")


    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.points) < self.max_points:
                self.points.append((x, y))
                print(f"Point {len(self.points)} enregistré : ({x}, {y})")
                if len(self.points) == self.max_points:
                    self.save_points()

    
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
    

    def is_in_zone(self, point, zone_idx):
        """Vérifie si un point (x, y) est dans une zone spécifique (0 ou 1)."""
        start_idx = zone_idx * 8
        if len(self.points) >= start_idx + 8:
            pts = np.array(self.points[start_idx:start_idx+8], np.int32)
            # Retourne True si le point est à l'intérieur ou sur le bord
            return cv2.pointPolygonTest(pts, point, False) >= 0
        return False