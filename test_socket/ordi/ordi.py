
import socket
from time import sleep

IP_Robot= '172.20.0.10'
PORT= 5555

sleep(10)
print("Tentative de connexion au robot ({})...".format(IP_Robot))

# On gere côté ordinateur
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    try:
        
        client.connect((IP_Robot, PORT))
        print("Connecté avec succès au robot ! En attente des messages...\n")

        #On écoute en boucle ce que le robot nous dit
        while True:
            # L'ordinateur attend de recevoir un message (jusqu'à 1024 octets)
            donnees_recues = client.recv(1024)

            # Si le colis est vide, c'est que la connexion a été coupée
            if not donnees_recues:
                print("La connexion avec le robot a été perdue.")
                break

            # On déballe le colis : on traduit les octets (0 et 1) en vrai texte
            message_texte = donnees_recues.decode('utf-8').strip()
            
            print("Message reçu du robot : {}".format(message_texte))

    except ConnectionRefusedError:
        print("Impossible de se connecter. Le programme du robot est-il bien lancé ?")
    except KeyboardInterrupt:
        print("\nArrêt manuel du programme sur l'ordinateur.")