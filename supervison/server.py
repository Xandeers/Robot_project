import threading
from flask import Flask, render_template
from flask_socketio import SocketIO

app= Flask(__name__)

Socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    """Page principal dashbord"""
    return render_template('index.html')
