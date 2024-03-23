from flask import Flask, render_template
from flask_socketio import SocketIO


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

socketio = SocketIO(app)


@app.route("/waiting_room", methods=["GET"])
def index():
    return render_template("waiting_room.html")
