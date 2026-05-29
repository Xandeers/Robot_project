import threading
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
Socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index():
    """Page principal dashbord"""
    return render_template('index.html')

def envoye(robot_x, robot_y, robot_angle, ball_x, ball_y, phase, ordre, enemies=None, allies=None, cible_x=None, cible_y=None, balle_en_jeu=True):
    """Gère l'envoi des données avec conversion stricte pour éviter le crash JSON"""
    
    if enemies is None: enemies = []
    if allies is None: allies = []

    try:
        
        data = {
            "robot_x": float(robot_x) if robot_x is not None else 0.0,
            "robot_y": float(robot_y) if robot_y is not None else 0.0,
            "robot_angle": float(robot_angle) if robot_angle is not None else 0.0,
            "ball_x": float(ball_x) if ball_x is not None else 0.0,
            "ball_y": float(ball_y) if ball_y is not None else 0.0,
            "phase": str(phase),
            "ordre": int(ordre) if ordre is not None else 3,
            "cible_x": float(cible_x) if cible_x is not None else 0.0,
            "cible_y": float(cible_y) if cible_y is not None else 0.0,
            "balle_en_jeu": bool(balle_en_jeu),
            
            # On nettoie aussi l'intérieur des listes
            "enemies": [{"id": int(e["id"]), "x": float(e["x"]), "y": float(e["y"])} for e in enemies],
            "allies": [{"id": int(a["id"]), "x": float(a["x"]), "y": float(a["y"])} for a in allies]
        }

        Socketio.emit('update', data)
        
    except Exception as e:
        print(f"[ERREUR WEB] Impossible d'envoyer les données : {e}")

def _demarrer_serveur():
    # allow_unsafe_werkzeug=True et use_reloader=False sont vitaux pour que Flask tourne sans bug dans un Thread OpenCV
    Socketio.run(app, host='0.0.0.0', port=5000, log_output=False, allow_unsafe_werkzeug=True, use_reloader=False)

def lancer_dashbord():
    """lance server web dans un thread diff"""
    threading.Thread(target=_demarrer_serveur, daemon=True).start()