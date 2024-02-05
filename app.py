from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, UserMixin, login_required, current_user
from flask_sock import Sock
from simple_websocket import ConnectionClosed
import requests
from collections import deque
import hashlib
import hmac
import json

app = Flask(__name__)
app.secret_key = "MYSECRET"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///accounts.db"

sock = Sock(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

secret_salt = "mattsSecretSauce"

# Store player information
players = {}

# Set of all client connections
clients = set()

# Previous messages before the player spawned are saved
message_cache = deque(maxlen=6)


class User(UserMixin, db.Model):
    """Class representing a user in the system.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user, should be unique.
        password (str): The hashed password of the user.

    Methods:
        to_dict(): Returns the user object as a dictionary.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def to_dict(self):
        """Converts the user object to a dictionary.

        Returns:
            dict: A dictionary containing user information.
        """
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


@login_manager.user_loader
def load_user(user_id: int):
    return User.query.filter_by(id=int(user_id)).first()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")
    user = User.query.filter_by(username=username).first()

    # Hash the users password
    password = hmac.new(
        secret_salt.encode(), password.encode(), hashlib.sha512
    ).hexdigest()

    if user and hmac.compare_digest(user.password, password):
        login_user(user)
        return redirect("/")
    return redirect("/login")


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return "Username already exists. Please choose a different username."

    # Hashing the user's password before adding it to the database
    password = hmac.new(
        secret_salt.encode(), password.encode(), hashlib.sha512
    ).hexdigest()
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect("/login")


@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html", player_id=current_user.id)


@app.route("/trivia", methods=["GET"])
@login_required
def trivia():
    requests.post("http://127.0.0.1:9999/trivia", json=current_user.to_dict())
    return redirect("http://127.0.0.1:9999/trivia")


@sock.route("/echo")
def echo(connection):
    if connection in clients or current_user.id in players:
        return

    clients.add(connection)
    players[current_user.id] = {"name": current_user.username, "id": current_user.id}
    print(f"{current_user.username} joined with connection {connection}")

    # Send the last few messages a player missed before they spawned
    for message in message_cache:
        connection.send(json.dumps(message))

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data["type"] == "playerUpdate":
                players[current_user.id].update(data["value"])
                send_to_all_clients({"type": "playersUpdate", "value": players})

            elif data["type"] == "playerRemoved":
                player_id = data["id"]
                if player_id in players:
                    del players[player_id]
                send_to_all_clients({"type": "playerRemoved", "id": player_id})

            elif data["type"] == "newMessage":
                text = data["text"]

                new_message = {
                    "type": "newMessage",
                    "text": text,
                    "id": current_user.id,
                    "name": current_user.username,
                }
                message_cache.append(new_message)
                send_to_all_clients(new_message)

        except (KeyError, ConnectionError, ConnectionClosed):
            clients.remove(connection)
            send_to_all_clients({"type": "playerRemoved", "id": current_user.id})
            del players[current_user.id]
            print(f"Removed connection {connection}")
            break


def send_to_all_clients(message: dict):
    """Sends a message to all connected clients.

    Args:
        message (dict): The message to be sent.
    """
    for client in clients:
        client.send(json.dumps(message))


if __name__ == "__main__":
    app.run(debug=True)
