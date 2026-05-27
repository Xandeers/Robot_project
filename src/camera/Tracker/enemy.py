import cv2
import numpy as np

class EnemyTracker:
    def __init__(self):
        self.backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
        
        self.min_area = 500  
        self.mask_radius_robot = 70 
        self.mask_radius_ball = 40 

    def get_enemies(self, frame, pos_idefix_pixel, pos_ball_pixel):
        """
        Analyse l'image pour trouver les robots adverses.
        Retourne une liste de coordonnées (x,y) et le masque de debug.
        """
        
        fgMask = self.backSub.apply(frame)

        # Supp les ombres 
        _, fgMask = cv2.threshold(fgMask, 200, 255, cv2.THRESH_BINARY)

        # Nettoye
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fgMask = cv2.morphologyEx(fgMask, cv2.MORPH_OPEN, kernel)
        fgMask = cv2.morphologyEx(fgMask, cv2.MORPH_CLOSE, kernel)

        #notre robot et la ball 
        if pos_idefix_pixel is not None:
            cv2.circle(fgMask, pos_idefix_pixel, self.mask_radius_robot, 0, -1)
        if pos_ball_pixel is not None:
            cv2.circle(fgMask, pos_ball_pixel, self.mask_radius_ball, 0, -1)

        #les taches blanches restantes
        contours, _ = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        enemies = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > self.min_area:
                # Centre gravité 
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    enemies.append((cx, cy))

        return enemies, fgMask

    def draw_enemies(self, frame, enemies):
        """Dessine des cibles sur les ennemis détectés"""
        for enemy in enemies:
            # cercle violet autour de l'ennemi
            cv2.circle(frame, enemy, 30, (255, 0, 255), 3)
            # Petite cible au centre
            cv2.drawMarker(frame, enemy, (255, 0, 255), cv2.MARKER_CROSS, 20, 2)
            cv2.putText(frame, "ENNEMI", (enemy[0] - 30, enemy[1] - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        return frame