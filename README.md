# 🤖 Projet Idefix - Système de Supervision et d'Intelligence Artificielle

voir section "how to start" pour le lancement 

**Auteur :** 
TRAD NEDIM P2006707
EL MOUKI OTMANE P2208286
MEZIANE MILOUD P2203783
ARAR FOUAD P2107921


Ce projet implémente un système complet de contrôle, de vision par ordinateur et de supervision pour un robot de compétition (Lego Mindstorms EV3). Le système repose sur une architecture distribuée où un PC gère les calculs lourds (Vision OpenCV, IA) et envoie des ordres bas niveau au robot physique via WiFi (UDP).

---


## Architecture du Système

Le projet est divisé en 3 grands blocs fonctionnels :

1. **Le Cerveau (PC local - Python) :**
   * Réception du flux vidéo des caméras du terrain via UDP.
   * **Vision par Ordinateur (OpenCV) :** * `BallTracker` : Détection de la balle (filtrage HSV optimisé et filtrage par surface `area`).
     * `RobotTracker` : Détection de la position et de l'angle d'Idefix (QR Code / Aruco).
     * `EnemyTracker` : Suivi des essaims alliés et ennemis.
   * **Moteur Physique (`TerrainIMG` & `Graph`) :** Transformation matricielle (Homographie) pour convertir les coordonnées de la caméra (Pixels) en coordonnées réelles sur le terrain (Centimètres), gestion de plusieurs zones de caméra.
   * **Intelligence Artificielle (`TrajectoryLogic`) :** Analyse la situation (balle en jeu, but, obstacles) et calcule l'ordre optimal (Contournement, Repli, Tir) avec anticipation.

2. **Le Robot (Lego EV3 - ev3dev / Python) :**
   * Écoute sur un port UDP pour recevoir les ordres en temps réel.
   * Exécution physique : Contrôle des moteurs (`AVANCE`, `DROITE`, `GAUCHE`, `STOP`).
   * **Feedback Audio :** Lecture de fichiers `.wav` (PCM 16-bit, Mono, 22050Hz) en tâche de fond pour les célébrations sans bloquer les roues.

3. **La Supervision (Web Dashboard - Flask / SocketIO) :**
   * Serveur asynchrone intégré au PC (Mode `threading`).
   * Radar tactique affichant le terrain en temps réel avec la position de toutes les entités (Idefix, Balle, Ennemis).
   * Affichage de la phase de jeu actuelle et de l'action en cours.

---

## Fonctionnalités Techniques Avancées

* **Filtre de Lissage (Alpha) :** Application d'une moyenne mobile exponentielle sur les coordonnées pour lisser les tremblements de la caméra et assurer une conduite fluide.
* **Mémoire Court-Terme (Hystérésis) :** Le système tolère les pertes de vision temporaires (reflets, flou de mouvement). Si la balle ou le robot disparaît pendant quelques millisecondes, l'IA utilise la dernière position connue pour éviter l'effet "essuie-glace".
* **Calibration Automatique / Manuelle :** Calibration du terrain en 16 points pour définir les zones de jeu et générer les matrices de transformation de perspective instantanément.

---

## Prérequis et Installation

### Sur le PC de contrôle
Les librairies suivantes sont nécessaires pour lancer le traitement d'image et le serveur web :

```bash
pip install -r required.txt
```
## Structure

```text
Robot_project/
│
├── main.py                     # Boucle principale (Vision + Serveur)
├── supervison/                 # Dossier de l'interface Web
│   ├── server.py               # Serveur Flask/SocketIO
│   └── templates/index.html    # Frontend (Radar tactique Javascript/Canvas)
│
├── src/
│   ├── camera/                 
│   │   ├── terrain.py          # Gestion des clics et de la déformation d'image
│   │   └── Tracker/            # Classes de détection OpenCV (ball, robot, enemy)
│   │
│   ├── terrain/                
│   │   └── graph.py            # Conversion Pixels -> CM et limites de la carte
│   │
│   ├── robot/logic/
│   │   └── trajectoire.py      # IA, choix de la phase de jeu et envoi UDP
│   │
│   └── audio/                  # Fichiers .wav convertis pour l'EV3
│
└── simulateur/                 # Prototype d'utilisation d'un réseau de neurones pour piloter l'IA
```

## Guide d'Utilisation

1. **Allumer et connecter le robot (Lego EV3) :**
   * S'assurer que l'EV3 est connecté au même réseau WiFi que le PC.
   * Ouvrir un terminal sur le PC et se connecter au robot via SSH :
     ```bash
     ssh robot@<IP_DU_ROBOT>
     ```
     *(Le mot de passe est : `maker`)*
   * Une fois connecté à l'EV3, se rendre dans le répertoire du projet et lancer le script d'écoute UDP :
     ```bash
     cd Robot_Project
     python3 main.py
     ```
     si probleme avec cette commande 
     ```bash
     PYTHONIOENCODING=utf-8 PYTHONPATH=. python3 test/robot_test/main_test.py
     ```


2. **Démarrer le système PC (Cerveau & Vision) :**
   * Ouvrir un nouveau terminal sur le PC local.
   * Exécuter le programme principal :
     ```bash
     python main.py
     ```
    si probleme de chemin 
    ```bash
     PYTHONPATH=. python3 test/test_total3.py
     ```

   * Si le terrain n'est pas calibré dans le fichier `.json`, cliquer sur les 16 points délimitant la zone de jeu directement sur la fenêtre OpenCV.

3. **Ouvrir le Radar Tactique (Supervision) :**
   * Ouvrir un navigateur web et se rendre sur `http://localhost:5000` (ou le port défini dans Flask).
   * Le radar passera du message "ATTENTE DATA" à l'affichage en temps réel dès que la calibration est terminée et que le robot est détecté.

