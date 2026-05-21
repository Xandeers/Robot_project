import cv2
import math
import numpy as np

class RobotTracker:
    def __init__(self, aruco_dict_type=cv2.aruco.DICT_4X4_50, robot_id=1):
        # Initialisation du dictionnaire ArUco. 
        # (Modifie DICT_4X4_50 selon le marqueur que tu as imprimé)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
        
        # Gestion de la version d'OpenCV pour les paramètres
        try:
            self.aruco_params = cv2.aruco.DetectorParameters()
        except AttributeError:
            self.aruco_params = cv2.aruco.DetectorParameters_create()
            
        # L'ID spécifique de ton robot
        self.robot_id = robot_id
        self.aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.aruco_params.adaptiveThreshWinSizeMin = 3
        self.aruco_params.adaptiveThreshWinSizeMax = 23
        self.aruco_params.adaptiveThreshWinSizeStep = 10
        self.aruco_params.minMarkerPerimeterRate = 0.03 # Accepte les marqueurs plus petits/lointains

    def getposition(self, frame):
        # ArUco fonctionne mieux sur des images en niveaux de gris
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Détection des marqueurs
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray, self.aruco_dict, parameters=self.aruco_params
        )

        robot_data = None

        if ids is not None:
            for i, aruco_id in enumerate(ids):
                # Si on trouve le bon robot
                if aruco_id[0] == self.robot_id:
                    # On récupère les 4 coins du marqueur détecté
                    # Ordre : [Haut-Gauche, Haut-Droite, Bas-Droite, Bas-Gauche]
                    c = corners[i][0]
                    
                    # 1. Calcul du centre (Moyenne des X et moyenne des Y)
                    center_x = int(np.mean(c[:, 0]))
                    center_y = int(np.mean(c[:, 1]))
                    center = (center_x, center_y)

                    # 2. Calcul de l'avant (Milieu entre coin 0 et coin 1)
                    front_x = int((c[0][0] + c[1][0]) / 2)
                    front_y = int((c[0][1] + c[1][1]) / 2)
                    front = (front_x, front_y)

                    # 3. Calcul de l'angle d'orientation
                    angle = math.degrees(math.atan2(front_y - center_y, front_x - center_x))

                    # On formate les données exactement comme ton ancien code
                    robot_data = {
                        "center": center,
                        "front": front,
                        "angle": angle
                    }
                    
                    break 

        return robot_data

    
    def drawRobot(self, frame, robot_data):
        """Dessine les infos du robot sur la frame vidéo"""
        if robot_data:
            center = robot_data["center"]
            front = robot_data["front"]
            
            # Dessine un point rouge au centre
            cv2.circle(frame, center, 5, (255, 0, 0), -1)
            
            # Dessine la flèche de direction en vert
            cv2.arrowedLine(frame, center, front, (0, 255, 0), 3, tipLength=0.3)
            
            # Affiche l'angle
            cv2.putText(frame, f"{int(robot_data['angle'])} deg", (center[0] + 25, center[1]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
        return frame