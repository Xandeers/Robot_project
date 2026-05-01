import socket

def creer_et_attendre_connexion():
   
    HOST = '0.0.0.0'  
    port=5555

    # Création du socket
    serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # On lie le socket au port et on écoute
    serveur.bind((HOST, port))
    serveur.listen()
    
 
    print("Démarrage du serveur... L'EV3 écoute sur le port {}.".format(port))
    print("En attente de l'ordinateur...")
    
    # Le programme attend ici l'arrivée du PC
    connexion, adresse = serveur.accept()
    
    
    print("Génial ! Ordinateur connecté depuis : {}".format(adresse))
    
    # On renvoie les variables pour pouvoir les utiliser dans le main.py
    return serveur, connexion


def envoyer_message(connexion, message):
    
  
    texte = "{}\n".format(message)
    
    # On encode et on envoie
    connexion.sendall(texte.encode('utf-8'))


def fermer_reseau(serveur, connexion):
   
    print("Fermeture des connexions réseau effectué")
    if connexion:
        connexion.close()
    if serveur:
        serveur.close()