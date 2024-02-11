from flask import Flask, render_template, request
from flask_socketio import SocketIO


def create_trivia_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET KEY"] = "secret"
    socketio = SocketIO(app)

    return app, socketio
