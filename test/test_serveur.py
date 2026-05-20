#fichier test du main du robot 

import socket
import time

# --- CONFIGURATION ---
# Remplace par l'adresse IP de ton robot EV3 sur le réseau Wi-Fi (ex: "192.168.x.x")
# Laisse "127.0.0.1" si tu fais tourner le robot et ce script sur le même PC
ROBOT_IP = "127.0.0.1" 
PORT = 9999

def envoyer_en_continu(sock, ordre, duree):
    """
    Envoie un ordre en boucle pendant X secondes.
    L'envoi se fait toutes les 0.1s pour éviter que le watchdog (0.5s) 
    du robot ne se déclenche et coupe les moteurs.
    """
    print(f"--- Envoi de l'ordre '{ordre}' pendant {duree} secondes ---")
    temps_fin = time.time() + duree
    
    while time.time() < temps_fin:
        # Envoi de l'ordre converti en string puis en bytes (utf-8)
        sock.sendto(str(ordre).encode('utf-8'), (ROBOT_IP, PORT))
        time.sleep(0.1) # Pause de 100ms entre chaque paquet

def main():
    # Création du socket UDP (SOCK_DGRAM)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"Démarrage du test vers {ROBOT_IP}:{PORT}")
    
    try:
        # Ordre 0 (AVANCE) pendant 3 secondes
        envoyer_en_continu(client, 0, 3)
        
        # Ordre 2 (PIVOTE DROITE) pendant 3 secondes
        envoyer_en_continu(client, 2, 1)
        # Ordre 3 (STOP) pendant 2 secondes
        envoyer_en_continu(client, 3, 1)
        
        envoyer_en_continu(client, 0, 3)
        
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur (Ctrl+C).")
        
    finally:
        print("Fin du script de test. Envoi d'un dernier ordre STOP (3).")
        # On envoie un dernier 3 pour être sûr que le robot s'arrête
        client.sendto(str(3).encode('utf-8'), (ROBOT_IP, PORT))
        client.close()

if __name__ == "__main__":
    main()