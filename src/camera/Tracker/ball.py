import cv2
import numpy as np

class BallTracker: 
    def __init__(self):
        # On force la tolérance au maximum pour les bleus sombres et grisâtres
        # Saturation descendue à 40, Luminosité descendue à 20 !
        self.lower_blue = np.array([90, 40, 20])   
        self.upper_blue = np.array([140, 255, 255])

    def get_position(self, frame):
        """Analyse l'image et renvoie (x, y) de la balle ou None."""
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Création du masque Bleu
        mask = cv2.inRange(hsv, self.lower_blue, self.upper_blue)
        
        # Nettoyage
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        # ⚠️ AFFICHAGE DE DEBUG OBLIGATOIRE POUR COMPRENDRE ⚠️
        cv2.imshow("Debug Masque Bleu", mask)

        # Détection des contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        ball_data = None

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            # FILTRE DE SURFACE AJUSTÉ : On descend à 10 pixels minimum !
            # (Ta balle est minuscule sur la caméra, 50 c'était peut-être trop grand)
            if 10 < area < 5000:
                ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)
                ball_data = {
                    "center": (int(x), int(y)),
                    "radius": int(radius)
                }
        
        return ball_data
    
    def draw_ball(self, frame, ball_data):
        """Dessine un cercle autour de la balle sur l'image."""
        if ball_data:
            center = ball_data["center"]
            display_radius = max(ball_data["radius"], 10) 
            
            # Cercle Vert bien visible
            cv2.circle(frame, center, display_radius, (0, 255, 0), 3)
            
        return frame