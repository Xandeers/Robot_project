import numpy as np 
import cv2



class Ball : 
    def __init__(self):
        self.lower_red1 = np.array([0, 120, 70])
        self.upper_red1 = np.array([10, 255, 255])
        self.lower_red2 = np.array([170, 120, 70])
        self.upper_red2 = np.array([180, 255, 255])

    
    def get_position(self, frame):
        """Analyse l'image et renvoie (x, y) de la balle ou None."""
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Créa du mask 
        mask1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask = mask1 + mask2

        # clean
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=2)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Détection des contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        ball_data = None # Par défaut, rien trouvé

        if contours:
            # On prend le plus gros objet rouge
            largest_contour = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)

            # On ne valide que si c'est assez grand pour être une balle
            if radius > 5:
                ball_data = {
                    "center": (int(x), int(y)),
                    "radius": int(radius)
                }
        
        return ball_data