import json
import re
from collections import defaultdict
import time
from flask import Flask, render_template, request, redirect
from flask_sock import Sock
from simple_websocket import ConnectionClosed
from flask_login import LoginManager, UserMixin, login_user, current_user
from .text import sample_paragraph

app = Flask(__name__)
app.secret_key = "MYSECRET"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
sock = Sock(app)

login_manager = LoginManager(app)


def is_plain_char(char: str) -> bool:
    return re.match(r'[a-zA-Z\s,.!?\'":;]', char)


@login_manager.user_loader
def load_user(username):
    return TypeRacer(username)

class TypeRacer(UserMixin):
    def __init__(self, username: str):
        self.id = username
        self.text = sample_paragraph()
        self.typed = []
        self.correct = 0
        self.incorrect = 0
        self.first_timestamp = time.perf_counter_ns()
        self.latest_timestamp = self.first_timestamp
        self.score = None


class TypeRaceRoom:
    def __init__(self):
        self.players_won = defaultdict(list)
        self.players_lost = defaultdict(list)
        self.type_racers = {}


rooms = defaultdict(TypeRaceRoom)


@app.route("/<string:game_id>", methods=["GET"])
def type_race(game_id: str):
    type_race_room = rooms[game_id]
    type_race_room.type_racers[current_user.id] = current_user

    return render_template(
        "type_race_game.html",
        username=current_user.id,
        game_id=game_id,
        text=current_user.text,
    )


@sock.route("/type_race/echo/<game_id>")
def echo(connection, game_id: str):
    type_race_room = rooms[game_id]

    while True:
        try:
            time.sleep(1/20)
            for p in type_race_room.type_racers.values():
                p.latest_timestamp = time.perf_counter_ns()
                p.wpm = round(
                    ((p.correct // 5) / (p.latest_timestamp - p.first_timestamp))
                    * 60e9,
                    2,
                )

            updates = {
                p.id: [p.wpm, p.correct, p.incorrect] for p in type_race_room.type_racers.values()
            }
            connection.send(json.dumps({"type": "updates", "updates": updates}))

        except (KeyError, ConnectionError, ConnectionClosed):
            break


@sock.route("/type_race/input/<game_id>")
def input(connection, game_id: str):
    type_race_room = rooms[game_id]

    my_progress = type_race_room.type_racers[current_user.id]
    progress = {
        "typed": my_progress.typed,
        "correct": my_progress.correct,
        "incorrect": my_progress.incorrect,
    }

    connection.send(json.dumps({"type": "progress", "progress": progress}))

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)
            user = type_race_room.type_racers[current_user.id]

            if "key" in data and user.score is None:
                if data["key"] == "Backspace" and len(user.typed) > 0:
                    if user.typed[-1] == user.text[len(user.typed) - 1]:
                        user.correct -= 1
                    else:
                        user.incorrect -= 1
                    user.typed.pop()
                elif is_plain_char(data["key"]) and not data["key"] == "Backspace":
                    user.typed.append(data["key"])

                    if user.typed[-1] == user.text[len(user.typed) - 1]:
                        user.correct += 1
                    else:
                        user.incorrect += 1

                my_progress = type_race_room.type_racers[current_user.id]
                progress = {
                    "typed": my_progress.typed,
                    "correct": my_progress.correct,
                    "incorrect": my_progress.incorrect,
                }

                connection.send(json.dumps({"type": "progress", "progress": progress}))

            if len(user.typed) == len(user.text) and user.score is None:
                user.score = user.wpm * user.correct / (user.correct + user.incorrect)
                place = 1
                players = type_race_room.type_racers.values()
                for p in players:
                    if p.score is not None and p.score > user.score:
                        place += 1

                connection.send(json.dumps({"type": "gameOver", "score": user.score, "place": place, "total": len(players)}))
                del type_race_room.type_racers[current_user.id]

        except (KeyError, ConnectionError, ConnectionClosed):
            break
