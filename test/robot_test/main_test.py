import socket
from time import sleep
from ev3dev2.motor import LargeMotor, OUTPUT_A,OUTPUT_B, OUTPUT_C, OUTPUT_D

from src.robot.module.moteur import *
from src.socket import creer_et_attendre_connexion, envoyer_message, fermer_reseau
from src.robot.module.ultrasonicSensor import *
from ev3dev2.sensor import INPUT_4
from ev3dev2.sound import Sound

# Configuration du serveur
HOST = "0.0.0.0"  # Écoute sur toutes les interfaces réseau du robot
PORT = 9999       # Le port dédié 

# Initialisation des moteurs
mAVD = LargeMotor(OUTPUT_A)
mAVG = LargeMotor(OUTPUT_B)
mARD = LargeMotor(OUTPUT_C)
mARG = LargeMotor(OUTPUT_D)

def executer_moteurs(action):
    """Traduit l'ordre reçu en mouvement physique"""

    if action == 0:
        print("MOTEURS : AVANCE")
        avanceVehicule_Uniform(mAVD, mAVG, mARD, mARG, 100)
        
    elif action == 1:
        print("MOTEURS : PIVOTE DROITE")
        rotation_Droite(mAVD, mAVG, mARD, mARG)

    elif action == 2:
        print("MOTEURS : PIVOTE DROITE")
        rotation_Droite(mAVD, mAVG, mARD, mARG)

    elif action == 3:
        print("MOTEURS : STOP")
        stopVehicule(mAVD, mAVG, mARD, mARG)

def main():
    
    serveur = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serveur.bind((HOST, PORT))
    
    serveur.settimeout(0.5)
    
    print(f"Robot EV3 allumé en UDP. En attente des ordres sur le port {PORT}...")
    
    try:
        while True:
            try:
                # Réception des paquets UDP 
                data, adresse = serveur.recvfrom(1024)
                
                # decode
                message = data.decode('utf-8').strip()
                
                # S'il y a plusieurs ordres collés, on prend le dernier
                if message:
                    derniere_action = int(message[-1]) 
                    executer_moteurs(derniere_action)
                    
            except socket.timeout:
                # Le PC ne répond plus depuis 0.5s !
                print("PERTE DE SIGNAL (Watchdog déclenché) -> ARRÊT MOTEURS !")
                executer_moteurs(3)
                
    except KeyboardInterrupt:
        print("\nArrêt manuel demandé par l'utilisateur.")
    except Exception as e:
        print(f"Erreur d'exécution : {e}")
    finally:
        print("Arrêt d'urgence des moteurs.")
        executer_moteurs(3) 
        serveur.close() 

if __name__ == "__main__":
    main()