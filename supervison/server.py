import threading
from flask import Flask, render_template
from flask_socketio import SocketIO

app= Flask(__name__)

Socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    """Page principal dashbord"""
    return render_template('index.html')

def envoye(robot_x, robot_y, robot_angle, ball_x, ball_y, phase, ordre):
    """gere l'envoye des donnée """

    data = {
        "robot_x": robot_x,
        "robot_y": robot_y,
        "robot_angle": robot_angle,
        "ball_x": ball_x,
        "ball_y":ball_y,
        "pahse": phase,
        "ordre": ordre
    }

    Socketio.emit('update',data)

def _demarrer_serveur():

    Socketio.run(app, host='0.0.0.0', port=5000, log_output=False)


def lancer_dashbord():
    """lance server web dans un thread diff"""

    threading.Thread(target=_demarrer_serveur, daemon=True).start()
    