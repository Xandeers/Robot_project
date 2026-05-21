import math
import socket

CENTRE_CAGE_X= 150
CENTRE_CAGE_Y= 390
DISTANCE_RECULE_CM =30
TOLERANCE_DST=15


class TrajectoryLogic:
    def __init__(self, ip_robot, port_robot=9999):
        self.ip_robot = ip_robot
        self.port_robot = port_robot
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.textes_ordres = {0: "AVANCE", 1: "DROITE", 2: "GAUCHE", 3: "STOP"}
        
        # param terrain
        self.centre_cage_x = CENTRE_CAGE_X
        self.centre_cage_y = CENTRE_CAGE_Y
        
        # distancce  deriere la balle 
        self.distance_recul = DISTANCE_RECULE_CM
        
        # Tolérance 
        self.tolerance_distance = TOLERANCE_DST
        