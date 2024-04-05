import json
import re
from collections import defaultdict
import time
from flask import Flask, render_template
from flask_sock import Sock
from simple_websocket import ConnectionClosed
from flask_login import LoginManager, UserMixin, current_user
from .text import sample_paragraph

app = Flask(__name__)
app.secret_key = "MYSECRET"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
sock = Sock(app)

login_manager = LoginManager(app)
users = {}


def is_plain_char(char: str) -> bool:
    return re.match(r'[a-zA-Z\s,.!?\'":;]', char)


@login_manager.user_loader
def load_user(username):
    if username not in users:
        users[username] = TypeRacer(username)
    return users[username]


class TypeRacer(UserMixin):
    def __init__(self, username: str):
        self.id = username
        self.text = sample_paragraph()
        self.typed = []
        self.correct = 0
        self.incorrect = 0
        self.wpm = 0
        self.first_timestamp = time.perf_counter_ns()
        self.latest_timestamp = self.first_timestamp
        self.score = None
        self.connected = False


class TypeRaceRoom:
    def __init__(self):
        self.type_racers = set()


rooms = defaultdict(TypeRaceRoom)


@app.route("/<string:game_id>", methods=["GET"])
def type_race(game_id: str):
    type_race_room = rooms[game_id]
    type_race_room.type_racers.add(current_user.id)

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
            time.sleep(1 / 20)
            current_user.latest_timestamp = time.perf_counter_ns()
            current_user.wpm = round(
                (
                    (current_user.correct // 5)
                    / (current_user.latest_timestamp - current_user.first_timestamp)
                )
                * 60e9,
                2,
            )

            updates = {
                id: [
                    users[id].wpm,
                    users[id].correct,
                    users[id].incorrect,
                    len(users[id].text),
                ]
                for id in type_race_room.type_racers
            }
            connection.send(json.dumps({"type": "updates", "updates": updates}))

        except (KeyError, ConnectionError, ConnectionClosed):
            break


@sock.route("/type_race/input/<game_id>")
def input(connection, game_id: str):
    type_race_room = rooms[game_id]
    current_user.connected = True

    progress = {
        "typed": current_user.typed,
        "correct": current_user.correct,
        "incorrect": current_user.incorrect,
    }

    connection.send(json.dumps({"type": "progress", "progress": progress}))

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if "key" in data and current_user.score is None:
                if data["key"] == "Backspace" and len(current_user.typed) > 0:
                    if (
                        current_user.typed[-1]
                        == current_user.text[len(current_user.typed) - 1]
                    ):
                        current_user.correct -= 1
                    else:
                        current_user.incorrect -= 1
                    current_user.typed.pop()
                elif is_plain_char(data["key"]) and not data["key"] == "Backspace":
                    current_user.typed.append(data["key"])

                    if (
                        current_user.typed[-1]
                        == current_user.text[len(current_user.typed) - 1]
                    ):
                        current_user.correct += 1
                    else:
                        current_user.incorrect += 1

                progress = {
                    "typed": current_user.typed,
                    "correct": current_user.correct,
                    "incorrect": current_user.incorrect,
                }

                connection.send(json.dumps({"type": "progress", "progress": progress}))

            if (
                len(current_user.typed) == len(current_user.text)
                and current_user.score is None
            ):
                current_user.score = (
                    current_user.wpm
                    * current_user.correct
                    / (current_user.correct + current_user.incorrect)
                )
                place = 1
                players = type_race_room.type_racers
                for id in players:
                    if (
                        users[id].score is not None
                        and users[id].score > current_user.score
                    ):
                        place += 1

                connection.send(
                    json.dumps(
                        {
                            "type": "gameOver",
                            "score": current_user.score,
                            "place": place,
                            "total": len(players),
                        }
                    )
                )

        except (KeyError, ConnectionError, ConnectionClosed):
            current_user.connected = False
            if all(not users[id].connected for id in type_race_room.type_racers):
                del rooms[game_id]
            break
