import cv2
import math
import numpy as np 

class RobotTracker:
    def __init__(self):
        
        self.lower_green = np.array([35, 100, 50])   
        self.upper_green = np.array([85, 255, 255])
        
        self.lower_blue = np.array([100, 100, 50])
        self.upper_blue = np.array([130, 255, 255])

    def getposition(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        kernel = np.ones((5, 5), np.uint8)

        def find_color_center(mask_in):
            mask_in = cv2.erode(mask_in, kernel, iterations=1)
            mask_in = cv2.dilate(mask_in, kernel, iterations=1)
            cnts, _ = cv2.findContours(mask_in, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if cnts:
                largest = max(cnts, key=cv2.contourArea)
                if cv2.contourArea(largest) > 50:
                    M = cv2.moments(largest)
                    if M["m00"] != 0:
                        return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            return None

        
        mask_v = cv2.inRange(hsv, self.lower_green, self.upper_green)
        mask_b = cv2.inRange(hsv, self.lower_blue, self.upper_blue)

        p_avant = find_color_center(mask_v)
        p_arriere = find_color_center(mask_b)

        robot_data = None

        if p_avant and p_arriere:
           
            center = ((p_avant[0] + p_arriere[0]) // 2, (p_avant[1] + p_arriere[1]) // 2)
            
            
            angle = math.degrees(math.atan2(p_avant[1] - p_arriere[1], p_avant[0] - p_arriere[0]))

            robot_data = {
                "center": center,
                "front": p_avant,
                "angle": angle
            }
    
        return robot_data

    
    def drawRobot(self, frame, robot_data):
        if robot_data:
            center = robot_data["center"]
            front = robot_data["front"]
            
            
            cv2.circle(frame, center, 20, (255, 255, 255), 2)
            
           
            cv2.arrowedLine(frame, center, front, (0, 255, 0), 3, tipLength=0.3)
            
            
            cv2.putText(frame, f"{int(robot_data['angle'])} deg", (center[0]+25, center[1]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
        return frame