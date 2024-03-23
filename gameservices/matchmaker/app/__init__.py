from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_sock import Sock
import json
from simple_websocket import ConnectionClosed, ConnectionError


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

db = SQLAlchemy()
sock = Sock(app)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"<Room {self.name}>"


app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///rooms.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@sock.route("/create_room")
def create_room(connection):
    while True:
        try:
            event = connection.receive()
            data = json.loads(event)
            room_name = data.get("room")
            if room_name:
                room = Room(name=room_name)
                db.session.add(room)
                db.session.commit()
                response = {"type": "create", "room": room.name}
                connection.send(json.dumps(response))
        except (KeyError, ConnectionError, ConnectionClosed):
            print("Lost room socket connection")
            break


@app.route("/")
def index():
    return render_template("waiting_room.html")
