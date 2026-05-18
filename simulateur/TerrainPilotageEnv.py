import gymnasium as gym
from gymnasium import spaces
import numpy as np

class TerrainPilotageEnv(gym.Env):
    """Environnement personnalisé Gymnasium basé sur les dimensions réelles du Graph"""
    
    def __init__(self, graph_instance):
        super(TerrainPilotageEnv, self).__init__()
        
        # On injecte ton instance de la classe Graph pour connaître ses dimensions
        self.graph = graph_instance
        
        # 1. L'ESPACE DES ACTIONS (Ce que l'IA peut décider)
        # Ici on définit 3 actions discrètes :
        # 0 = Aller tout droit (avancer sur l'axe Y)
        # 1 = Tourner à gauche (aller vers les X négatifs)
        # 2 = Tourner à droite (aller vers les X positifs)
        self.action_space = spaces.Discrete(3)
        
        # 2. L'ESPACE DES OBSERVATIONS (Ce que l'IA reçoit pour prendre sa décision)
        # L'IA a juste besoin de connaître sa position actuelle [X, Y] en cm.
        # On définit les bornes minimales [0, 0] et maximales [width, length]
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0], dtype=np.float32),
            high=np.array([float(self.graph.width), float(self.graph.length)], dtype=np.float32),
            dtype=np.float32
        )
        
        # Définition d'un point "Cible" virtuel à atteindre (ex: le centre du terrain)
        self.cible_x = self.graph.width / 2
        self.cible_y = self.graph.length / 2
        
        # Variables internes pour suivre la voiture pendant la simulation
        self.car_x = 0.0
        self.car_y = 0.0

    def reset(self, seed=None, options=None):
        """Réinitialise l'environnement pour une nouvelle partie d'entraînement"""
        super().reset(seed=seed)
        
        # On positionne la voiture de manière aléatoire sur le terrain pour débuter
        # (en laissant une petite marge de 20cm par rapport aux bords)
        self.car_x = np.random.uniform(20.0, float(self.graph.width) - 20.0)
        self.car_y = np.random.uniform(20.0, float(self.graph.length) - 20.0)
        
        # On retourne l'état initial sous forme de tableau NumPy (Float32 requis par PyTorch)
        state = np.array([self.car_x, self.car_y], dtype=np.float32)
        return state, {}

    def step(self, action):
        """Exécute une action demandée par l'IA et calcule les conséquences"""
        
        # Physique fictive simple : la voiture se déplace de 5 cm par étape (Step)
        pas_cm = 5.0 
        
        if action == 0:    # Tout droit
            self.car_y += pas_cm
        elif action == 1:  # Gauche
            self.car_x -= pas_cm
        elif action == 2:  # Droite
            self.car_x += pas_cm
            
        # 3. SÉCURITÉ : On utilise TA classe Coordonee et TA méthode is_inside !
        position_actuelle = Coordonee(self.car_x, self.car_y)
        en_piste = self.graph.is_inside(position_actuelle)
        
        # 4. CALCUL DE LA RÉCOMPENSE (Le système de notation)
        terminated = False
        
        if not en_piste:
            # Si elle sort du terrain de $301 \times 390$, grosse punition et fin de la partie
            reward = -100.0
            terminated = True
        else:
            # Si elle est sur la piste, on calcule sa distance par rapport au centre (la cible)
            distance_a_la_cible = np.sqrt((self.car_x - self.cible_x)**2 + (self.car_y - self.cible_y)**2)
            
            # Plus la distance est petite, plus la récompense est grande (max +10 points)
            reward = 10.0 - (distance_a_la_cible / 10.0)
            
            # Si elle est vraiment très proche du centre (moins de 5cm), elle a gagné !
            if distance_a_la_cible < 5.0:
                reward += 50.0
                terminated = True
                
        truncated = False # Utilisé pour les limites de temps (optionnel ici)
        
        # On prépare l'état suivant
        state = np.array([self.car_x, self.car_y], dtype=np.float32)
        
        return state, reward, terminated, truncated, {}