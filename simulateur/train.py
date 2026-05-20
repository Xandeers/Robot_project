import sys
import os
# On force Python à regarder dans le dossier parent (Robot_project)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from TerrainPilotageEnv import TerrainPilotageEnv
from src.terrain.graph import Graph

# 1. Instancier ton Graph (le terrain de 301x390 cm)
# On imagine que tu as déjà créé ton objet et configuré tes matrices
mon_graph = Graph(x_widthCM=301, y_lengthCM=390)

# 2. Créer ton environnement personnalisé
env = TerrainPilotageEnv(mon_graph)

# 3. VERIFICATION (Très important)
# Cette fonction vérifie que ton environnement respecte bien les règles de Gymnasium
print("Vérification de l'environnement en cours...")
check_env(env)
print("Environnement valide ! 👍")

# 4. CONFIGURER LE CERVEAU (PyTorch + PPO)
# - "MlpPolicy" indique à PyTorch de créer un réseau de neurones classique (idéal pour des coordonnées X,Y)
# - env est ton simulateur personnalisé
# - verbose=1 permet d'afficher les statistiques d'apprentissage dans le terminal
model = PPO("MlpPolicy", env, verbose=1)

# 5. LANCER L'ENTRAÎNEMENT
# L'IA va faire des milliers de tentatives. 100 000 ou 200 000 étapes (timesteps) 
# sont un bon début pour un problème simple comme celui-ci.
print("Lancement de l'entraînement de l'IA...")
model.learn(total_timesteps=1000000)

# 6. SAUVEGARDER LE MODÈLE
# Une fois entraîné, on sauvegarde les "poids" du réseau de neurones dans un fichier
model.save("mon_pilote_ia")
print("IA entraînée avec succès et sauvegardée sous le nom 'mon_pilote_ia' !")