import sys
import os
import time

MAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if MAIN_DIR not in sys.path:
    sys.path.insert(0, MAIN_DIR)

import gymnasium as gym
from stable_baselines3 import PPO
from src.terrain.graph import Graph # Remplace par ton import si nécessaire

def test_ia_visuel():
    # 1. Création d'une instance du terrain (comme dans ton train.py)
    # Ajuste les dimensions 301x390 selon ton projet
    graph_instance = Graph(x_widthCM=301, y_lengthCM=390) 
    
    # 2. Initialisation de l'environnement avec le mode graphique activé
    print("Initialisation de l'environnement graphique...")
    from simulateur.TerrainPilotageEnv import TerrainPilotageEnv
    env = TerrainPilotageEnv(graph_instance, render_mode="human")
    
    # 3. Chargement du modèle entraîné
    nom_modele = "mon_pilote_ia.zip"
    if not os.path.exists(nom_modele):
        print(f"⚠️ Erreur : Le fichier '{nom_modele}' est introuvable. Entraîne d'abord l'IA !")
        return
        
    print(f"Chargement du cerveau '{nom_modele}'...")
    model = PPO.load(nom_modele)
    
    # 4. Lancement de la simulation de test
    obs, info = env.reset()
    terminated = False
    truncated = False
    
    print("Début du test visuel. Regarde la fenêtre Pygame ! (CTRL+C dans le terminal pour quitter)")
    
    try:
        while not (terminated or truncated):
            # L'IA choisit l'action en fonction de ce qu'elle voit (l'observation)
            # deterministic=True force l'IA à être précise et à ne pas faire de mouvements au hasard
            action, _states = model.predict(obs, deterministic=True)
            
            # On exécute l'action dans l'environnement
            obs, reward, terminated, truncated, info = env.step(action)
            
            # Petite pause pour que tes yeux humains puissent suivre l'action (30 FPS)
            time.sleep(0.03)
            
        print("Fin de la partie (But marqué ou sortie de piste) !")
        
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur.")
    finally:
        env.close()

if __name__ == "__main__":
    test_ia_visuel()