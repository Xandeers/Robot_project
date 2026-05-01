import cv2
import numpy as np 



class RobotTracker :
    def __init__(self):
    
        self.lower_green = np.array([35, 100, 50])   
        self.upper_green = np.array([85, 255, 255])


    def getposition(self, frame):
        """Analyse l'image et renvoie (x, y) du robot ou None. """

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, self.lower_green, self.upper_green)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)
    
     #Debug pour voir si le robot est bien "blanc" sur le masque
        cv2.imshow("Debug Masque Robot", mask)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
        robot_data = None 

        if contours:
        
            largest_contour = max(contours, key=cv2.contourArea)
    
            ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)

        # On ajuste le rayon minimum selon la taille réelle de ton robot à l'image
        if radius > 5: # Augmenté un peu pour éviter les faux positifs
            robot_data = {
                "center": (int(x), int(y)),
                "radius": int(radius),
                "area": cv2.contourArea(largest_contour)
            }
    
        return robot_data


    def drawRobot(self,frame,robot_data):

        if robot_data :
            center = robot_data["center"]
            display_radius = max(robot_data["radius"],10)
        
            cv2.circle(frame, center, display_radius, (0, 255, 0), 3)
            
            #Centre en ROUGE (-1 pour remplir le cercle)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
            
        return frame