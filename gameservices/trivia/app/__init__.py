import os
from flask import Flask, render_template, request, session
from flask_login import LoginManager, UserMixin, current_user
from flask_socketio import SocketIO
from .trivia_game_server import trivia_game
from .questions import TriviaDB

app = Flask(__name__)
app.secret_key = "MYSECRET"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
socketio = SocketIO(app)

csv_file_path = os.path.join(
    os.path.dirname(__file__), "static", "trivia_questions.csv"
)
db = TriviaDB(csv_file_path)

login_manager = LoginManager(app)

users_s = {}


@login_manager.user_loader
def load_user(username):
    if username not in users_s:
        users_s[username] = User(username)
    return users_s[username]


class User(UserMixin):
    def __init__(self, username):
        self.id = username


users = {}
user_queue = []
game_info = {"num_questions": 10, "timer": 10, "game_id": "1234"}


@app.route("/<string:gameid>", methods=["GET"])
def index(gameid: str):
    game_info["game_id"] = gameid
    return render_template("trivia_waiting_room.html", username=current_user.id)


@socketio.on("connect", namespace="/trivia")
def handle_connect():
    print("Client connected to /trivia:", request.sid)


@app.route("/trivia/game")
def render_game():
    return render_template("trivia_game.html", game_id=game_info["game_id"])


@socketio.on("start_game", namespace="/trivia")
def start_game():
    print("Starting the game")
    socketio.start_background_task(
        trivia_game(socketio, users.copy(), game_info.copy(), db)
    )
    socketio.emit(
        "switch_page",
        {"url": "trivia/game", "game_id": game_info["game_id"]},
        namespace="/trivia",
    )


@socketio.on("username", namespace="/trivia")
def get_username(username):
    session["username"] = username
    users[username] = request.sid
    user_queue.append(request.sid)
    print("Received username", username)
    update_users()
    socketio.emit(
        "num_questions",
        game_info["num_questions"],
        namespace="/trivia",
        room=request.sid,
    )
    socketio.emit("timer", game_info["timer"], namespace="/trivia", room=request.sid)
    if len(users) == 1:
        update_party_leader()


@socketio.on("disconnect", namespace="/trivia")
def handle_disconnect():
    if session.get("username") in users:
        print("Client disconnected from /trivia:", request.sid)
        users.pop(session.get("username"))
        user_queue.remove(request.sid)
        update_users()
        update_party_leader()


@socketio.on("num_questions", namespace="/trivia")
def update_num_questions(new_num):
    game_info["num_questions"] = new_num
    socketio.emit("num_questions", game_info["num_questions"], namespace="/trivia")


@socketio.on("timer", namespace="/trivia")
def update_timer(new_timer):
    game_info["timer"] = int(new_timer)
    socketio.emit("timer", game_info["timer"], namespace="/trivia")


def update_users():
    socketio.emit("user_list", list(users.keys()), namespace="/trivia")


def update_party_leader():
    if len(user_queue) > 0:
        socketio.emit("party_leader", room=user_queue[0], namespace="/trivia")
