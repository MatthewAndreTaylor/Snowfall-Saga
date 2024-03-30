import os
from flask import Flask, render_template, request
from flask_login import LoginManager, UserMixin, current_user
from flask_socketio import SocketIO, join_room
from .questions import TriviaDB
import requests
import random

app = Flask(__name__)
app.secret_key = "MYSECRET"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
socketio = SocketIO(app)

csv_file_path = os.path.join(
    os.path.dirname(__file__), "static", "trivia_questions.csv"
)
db = TriviaDB(csv_file_path)

users = {}
user_queue = []
game_info = {"num_questions": 10, "timer": 10}

login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(username):
    if username not in users:
        users[username] = User(username)
    return users[username]


class User(UserMixin):
    def __init__(self, username):
        self.id = username


@app.route("/<string:game_id>", methods=["GET"])
def index(game_id: str):
    print("got a connection")
    return render_template(
        "trivia_waiting_room.html", username=current_user.id, game_id=game_id
    )


@socketio.on("connect", namespace="/trivia")
def handle_connect():
    print("Client connected to /trivia:", request.sid)


@app.route("/trivia/game/<string:game_id>")
def render_game(game_id: str):
    return render_template("trivia_game.html", game_id=game_id)


@socketio.on("start_game", namespace="/trivia")
def start_game(game_id):
    print("Starting the game")
    socketio.start_background_task(
        trivia_game(socketio, users.copy(), game_info.copy(), game_id, db)
    )
    socketio.emit(
        "switch_page",
        {"url": "", "game_id": f"trivia/game/{game_id}"},
        namespace="/trivia",
    )


@socketio.on("username", namespace="/trivia")
def get_username(username):
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
    print("Client disconnected from /trivia:", request.sid)
    users.pop(current_user.id)
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


def trivia_game(
    socketio: SocketIO, users: dict, game_info: dict, game_id: str, db: TriviaDB
):
    points = {}
    namespace = "/trivia/game/" + game_id

    def update_room_user_list():
        socketio.emit(
            "user_list",
            list(users.keys()),
            room=game_id,
            namespace=namespace,
        )

    @socketio.on("connect", namespace=namespace)
    def connect():
        print("Client joined the game")
        socketio.emit("hi", namespace=namespace)
        join_room(game_id)
        print(f"Users in room {game_id}, {users.keys()}")
        socketio.emit(
            "user_list", list(users.keys()), room=request.sid, namespace=namespace
        )

    @socketio.on("disconnect", namespace=namespace)
    def disconnect():
        # Remove the user from users
        print(f"Users in room {game_id}, {users.keys()}")
        if current_user.id in users:
            users.pop(current_user.id)
            update_room_user_list()

    @socketio.on("register", namespace=namespace)
    def register_user(username):
        points[username] = 0
        if len(points) == len(users):
            socketio.start_background_task(run_main_game)

    def run_main_game():
        question_number = 1
        while question_number <= game_info["num_questions"]:
            categories = db.get_categories()
            question = db.get_question_by_category(random.choice(categories))
            socketio.emit("question", question, room=game_id, namespace=namespace)

            answers = {}

            @socketio.on("answer", namespace=namespace)
            def receive_answer(answer):
                if current_user.id in users:
                    print("Received answer from", current_user.id)
                    answers[current_user.id] = answer

            while len(answers) < len(users):
                socketio.sleep(1)

            print("Received answers", answers)
            print("Correct answer", question["correct"])
            for user in users:
                if answers[user] == question["correct"]:
                    points[user] += 10
                    socketio.emit(
                        "correct", points, room=users[user], namespace=namespace
                    )
                    print("Correct answer", user, "Got some points")
                else:
                    socketio.emit(
                        "incorrect", points, room=users[user], namespace=namespace
                    )

            question_number += 1

        send_points(points)


def send_points(points):
    requests.post("http://127.0.0.1:5000/points", json=points)
