import sys
import os
import math

MAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if MAIN_DIR not in sys.path:
    sys.path.insert(0, MAIN_DIR)

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from src.terrain.graph import Coordonee

class TerrainPilotageEnv(gym.Env):
    metadata = {"render_modes": ["human"]}
    
    def __init__(self, graph_instance, render_mode=None):
        super(TerrainPilotageEnv, self).__init__()
        self.graph = graph_instance
        self.render_mode = render_mode
        
        # 4 Actions de Tank : 0=Avance, 1=Recule, 2=Pivote Gauche, 3=Pivote Droite
        self.action_space = spaces.Discrete(4)
        
        # 4 Variables Relatives (Le Radar Relatif)
        # [0]: Distance Cible, [1]: Cosinus (Face/Dos), [2]: Sinus (Gauche/Droite), [3]: Distance Mur proches
        limite_max = float(max(self.graph.width, self.graph.length))
        self.observation_space = spaces.Box(
            low=np.array([0.0, -1.0, -1.0, 0.0], dtype=np.float32),
            high=np.array([limite_max, 1.0, 1.0, limite_max], dtype=np.float32),
            dtype=np.float32
        )
        
        self.but_x = self.graph.width / 2
        self.but_y = 20.0
        
        self.window = None
        self.clock = None
        
        self.dist_cible_prec = 0.0
        self.dist_balle_but_prec = 0.0

    def calcul_trajectoire(self):
        """Calcule le point vert stratégique derrière ou à côté de la balle"""
        vx = self.but_x - self.ball_x
        vy = self.but_y - self.ball_y
        dist_bg = np.sqrt(vx**2 + vy**2)

        if dist_bg < 0.1:
            return self.ball_x, self.ball_y

        ux, uy = vx / dist_bg, vy / dist_bg
        frappe_x = self.ball_x - (ux * 20.0)
        frappe_y = self.ball_y - (uy * 20.0)

        rx = self.car_x - self.ball_x
        ry = self.car_y - self.ball_y

        produit_scalaire = (rx * ux) + (ry * uy)

        if produit_scalaire > -5.0:
            perp_x, perp_y = -uy, ux
            if (rx * perp_x + ry * perp_y) > 0:
                cible_x = self.ball_x + (perp_x * 35.0)
                cible_y = self.ball_y + (perp_y * 35.0)
            else:
                cible_x = self.ball_x - (perp_x * 35.0)
                cible_y = self.ball_y - (perp_y * 35.0)
        else:
            cible_x = frappe_x
            cible_y = frappe_y

        return cible_x, cible_y

    def _generer_observation(self, dist_cible):
        """Génère le radar relatif pour simplifier la vie de l'IA"""
        if dist_cible > 0.1:
            # Vecteur unitaire vers la cible
            ux_t = (self.cible_x - self.car_x) / dist_cible
            uy_t = (self.cible_y - self.car_y) / dist_cible
            
            # Vecteur de direction du robot (0° = vers le haut)
            ux_r = math.sin(self.angle)
            uy_r = -math.cos(self.angle)
            
            # Cosinus Relatif (Produit scalaire)
            cos_rel = (ux_r * ux_t) + (uy_r * uy_t)
            
            # Sinus Relatif (Produit vectoriel 2D)
            sin_rel = (ux_r * uy_t) - (uy_r * ux_t)
        else:
            cos_rel = 1.0
            sin_rel = 0.0

        # Calcul de la distance au mur le plus proche
        dist_murs = [
            self.car_x,                           # Mur Gauche
            self.graph.width - self.car_x,        # Mur Droit
            self.car_y,                           # Mur Haut
            self.graph.length - self.car_y        # Mur Bas
        ]
        dist_mur_proche = float(min(dist_murs))

        return np.array([dist_cible, cos_rel, sin_rel, dist_mur_proche], dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.car_x = np.random.uniform(50.0, self.graph.width - 50.0)
        self.car_y = np.random.uniform(50.0, self.graph.length - 50.0)
        self.angle = np.random.uniform(-math.pi, math.pi)
        
        self.ball_x = self.graph.width / 2
        self.ball_y = self.graph.length / 2
        
        self.cible_x, self.cible_y = self.calcul_trajectoire()
        
        self.dist_cible_prec = np.sqrt((self.car_x - self.cible_x)**2 + (self.car_y - self.cible_y)**2)
        self.dist_balle_but_prec = np.sqrt((self.ball_x - self.but_x)**2 + (self.ball_y - self.but_y)**2)
        
        state = self._generer_observation(self.dist_cible_prec)
        
        if self.render_mode == "human":
            self.render()
            
        return state, {}

    def step(self, action):
        pas_cm = 7.0        
        rot_pas = math.radians(12) 
        dx, dy = 0.0, 0.0
        
        # EXECUTION DES ACTIONS MOTEURS (TANK)
        if action == 0:   # AVANCE
            dx = pas_cm * math.sin(self.angle)
            dy = -pas_cm * math.cos(self.angle)
        elif action == 1: # RECULE
            dx = -pas_cm * math.sin(self.angle)
            dy = pas_cm * math.cos(self.angle)
        elif action == 2: # PIVOTE GAUCHE
            self.angle -= rot_pas
        elif action == 3: # PIVOTE DROITE
            self.angle += rot_pas
            
        self.angle = (self.angle + math.pi) % (2 * math.pi) - math.pi
            
        self.car_x += dx
        self.car_y += dy
        
        # GEOMETRIE DES CONTACTS (DRIBBLE)
        dist_robot_balle = np.sqrt((self.car_x - self.ball_x)**2 + (self.car_y - self.ball_y)**2)
        balle_a_bouge = False
        if dist_robot_balle < 15.0:
            self.ball_x += dx * 1.4
            self.ball_y += dy * 1.4
            balle_a_bouge = True
            
        # RECALCUL EN TEMPS REEL DE LA TRAJECTOIRE
        self.cible_x, self.cible_y = self.calcul_trajectoire()
        dist_cible_actuelle = np.sqrt((self.car_x - self.cible_x)**2 + (self.car_y - self.cible_y)**2)
        dist_balle_but_actuelle = np.sqrt((self.ball_x - self.but_x)**2 + (self.ball_y - self.but_y)**2)

        # Génération du nouvel état radar
        state = self._generer_observation(dist_cible_actuelle)
        cos_rel = state[1]  
        dist_mur = state[3] 

        # --- RECOMPENSES DU RADAR RELATIF ---
        reward = -0.3  # Pénalité de temps
        
        # Gain d'alignement brut (+3.0 si face au point vert, -3.0 si dos au point vert)
        reward += cos_rel * 3.0
        
        # Gain de rapprochement (uniquement si aligné et en marche avant)
        diff_cible = self.dist_cible_prec - dist_cible_actuelle
        if action == 0 and cos_rel > 0.8:
            reward += diff_cible * 8.0
            
        # Gain de poussée de la balle vers l'objectif
        if balle_a_bouge:
            diff_balle = self.dist_balle_but_prec - dist_balle_but_actuelle
            if diff_balle > 0:
                reward += diff_balle * 12.0 
                
        self.dist_cible_prec = dist_cible_actuelle
        self.dist_balle_but_prec = dist_balle_but_actuelle

        # --- SECTIONS SECURITES ET SORTS DU TERRAIN ---
        terminated = False
        marge_mur = 25.0
        en_piste = self.graph.is_inside(Coordonee(self.car_x, self.car_y))
        
        if not en_piste:
            reward -= 1000.0  # Punition radicale pour être sorti
            terminated = True
        elif dist_mur < marge_mur:
            # Pénalité progressive en s'approchant des lignes blanches
            reward -= (marge_mur - dist_mur) * 2.0
            
        if dist_balle_but_actuelle < 30.0:
            reward += 1000.0  # Le but ultime !
            terminated = True
            
        if self.render_mode == "human":
            self.render()
            
        # CORRECTION CRITICAL : Cast de sécurité en float Python pur pour Gymnasium check_env
        reward = float(reward)
            
        return state, reward, terminated, False, {}

    def render(self):
        echelle = 2.0 
        if self.window is None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((int(self.graph.width * echelle), int(self.graph.length * echelle)))
            pygame.display.set_caption("IA : Radar Relatif Actif")
            self.clock = pygame.time.Clock()

        self.window.fill((255, 255, 255))
        pygame.draw.rect(self.window, (220, 220, 220), (0, 0, self.graph.width*echelle, self.graph.length*echelle), int(25*echelle))
        
        cages_px = (int(self.but_x * echelle), int(self.but_y * echelle))
        pygame.draw.circle(self.window, (255, 0, 0), cages_px, 30)
        
        if hasattr(self, 'cible_x'):
            cible_px = (int(self.cible_x * echelle), int(self.cible_y * echelle))
            pygame.draw.circle(self.window, (0, 200, 0), cible_px, 10)
        
        balle_px = (int(self.ball_x * echelle), int(self.ball_y * echelle))
        pygame.draw.circle(self.window, (255, 165, 0), balle_px, 12)
        
        voiture_px = (int(self.car_x * echelle), int(self.car_y * echelle))
        pygame.draw.circle(self.window, (0, 0, 255), voiture_px, 15)
        
        avant_x = voiture_px[0] + 20 * math.sin(self.angle)
        avant_y = voiture_px[1] - 20 * math.cos(self.angle)
        pygame.draw.line(self.window, (0, 255, 0), voiture_px, (int(avant_x), int(avant_y)), 3)

        pygame.event.pump()
        pygame.display.update()
        self.clock.tick(30)
        
    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()
            self.window = None