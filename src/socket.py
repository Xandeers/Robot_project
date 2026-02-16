#!/usr/bin/env python3
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.sensor import INPUT_4 
import socket
import time


from moteur import demarrer_robot, arreter_robot

us = UltrasonicSensor(INPUT_4)

HOST = '0.0.0.0'  
PORT = 65432      

print("Démarrage du serveur sur l'EV3...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"L'EV3 écoute sur le port {PORT}. En attente de l'ordinateur...")
    
    connexion, adresse = s.accept()
    
    with connexion:
        print(f"Génial ! Ordinateur connecté depuis : {adresse}")
        
        # ON LANCE LES MOTEURS ICI (grâce à la fonction du main.py)
        demarrer_robot() 
        
        try:
            while True:
                distance = us.distance_centimeters
                message = f"{round(distance, 1)}\n"
                
                # On envoie la distance au PC
                connexion.sendall(message.encode('utf-8'))
                
                # Si obstacle : on appelle la fonction stop de main.py !
                if distance < 20:
                    arreter_robot()
                    connexion.sendall("OBSTACLE\n".encode('utf-8'))
                    break # Fin de la boucle
                
                time.sleep(0.1)
                
        except (ConnectionResetError, BrokenPipeError):
            print("L'ordinateur s'est déconnecté.")
            arreter_robot() # Sécurité : on arrête si le PC coupe
        except KeyboardInterrupt:
            arreter_robot()
            print("Arrêt manuel.")