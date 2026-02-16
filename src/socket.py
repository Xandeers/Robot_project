#!/usr/bin/env python3
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.sensor import INPUT_4 
import socket
import time


from moteur import demarrer_robot, arreter_robot

#!/usr/bin/env python3
import socket

def creer_et_attendre_connexion(port=65432):
   
    HOST = '0.0.0.0'  
    
    #Création du socket
    serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # On lie le socket au port et on écoute
    serveur.bind((HOST, port))
    serveur.listen()
    print(f"Démarrage du serveur... L'EV3 écoute sur le port {port}.")
    print("En attente de l'ordinateur...")
    
    # Le programme attend ici l'arrivée du PC
    connexion, adresse = serveur.accept()
    print(f"Génial ! Ordinateur connecté depuis : {adresse}")
    
    # On renvoie les variables pour pouvoir les utiliser dans le main.py
    return serveur, connexion


def envoyer_message(connexion, message):
    """
    Prend la connexion active et envoie le message à l'ordinateur.
    """
    # On convertit le message en texte et on ajoute un retour à la ligne
    texte = f"{message}\n"
    # On encode et on envoie
    connexion.sendall(texte.encode('utf-8'))


def fermer_reseau(serveur, connexion):
    """
    Ferme proprement les connexions réseau pour éviter les bugs au prochain lancement.
    """
    print("Fermeture des connexions réseau...")
    if connexion:
        connexion.close()
    if serveur:
        serveur.close()