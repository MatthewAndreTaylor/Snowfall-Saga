import json
import random
from collections import defaultdict

from flask import Flask, Blueprint, render_template, request
from flask_sock import Sock
from simple_websocket import ConnectionClosed
from gameservices.type_race.app.user import User
from gameservices.type_race.app.text import get_text

type_race_game = Blueprint(
    "type_race_game",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets/type_race",
)

sock = Sock(type_race_game)

players_waiting = {}
clients = set()

text = {}

current_user = {"username": "JOE", "game_id": 0}

players = defaultdict(dict)
players_won = defaultdict(list)
players_lost = defaultdict(list)


def create_type_race_app():
    app = Flask(__name__)
    app.secret_key = "MYSECRET"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    with app.app_context():
        app.register_blueprint(type_race_game)

    return app


@type_race_game.route("/type_race", methods=["GET", "POST"])
def type_race():
    if request.method == "POST":
        print("Got HERE")
        current_user["username"] = request.json["username"]
    else:
        current_user["username"] = "JOE" + str(random.randint(1, 10000))
    return render_template(
        "type_race_waiting_room.html",
        username=current_user["username"],
        gameId=current_user["game_id"],
    )


@type_race_game.route("/type_race/game/<game_id>", methods=["GET"])
def send_to_game(game_id):
    return render_template("type_race_game.html", text=text[int(game_id)][0])


@sock.route("/type_race")
def waiting_room(connection):
    print("Got a connection")
    clients.add(connection)

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data["type"] == "username":
                players_waiting[connection] = data["username"]
                update_player_list()

            elif data["type"] == "startGame":
                text[current_user["game_id"]] = get_text(3)
                current_user["game_id"] += 1
                for client in clients:
                    client.send(
                        json.dumps({"type": "switchPage", "url": "type_race/game"})
                    )

        except (KeyError, ConnectionError, ConnectionClosed):
            clients.remove(connection)
            players_waiting.pop(connection)
            update_player_list()
            break


def update_player_list():
    for client in players_waiting:
        client.send(
            json.dumps({"type": "playerList", "data": list(players_waiting.values())})
        )


@sock.route("/type_race/game/<game_id>")
def run_game(connection, game_id):
    game_id = int(game_id)
    print("got a connection")
    if connection in clients:
        return

    clients.add(connection)
    players_here = players[game_id]

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data["type"] == "playerUpdate":
                print("Received player update from", players_here[connection].username)
                words_typed = (data["correct"] - players_here[connection].correct) / 5

                if data["correct"] > 0:
                    players_here[connection].wpm_queue.append(words_typed * 120)
                    players_here[connection].wpm = round(
                        sum(players_here[connection].wpm_queue)
                        / len(players_here[connection].wpm_queue)
                    )

                players_here[connection].correct = data["correct"]
                print("correct:", data["correct"], "wpm", players_here[connection].wpm)
                update = {
                    p.username: (p.correct // 2, p.wpm, p.standings)
                    for p in players_here.values()
                }
                update["type"] = "playerUpdate"
                connection.send(json.dumps(update))

            elif data["type"] == "username":
                players_here[connection] = User(data["username"])

            elif data["type"] == "done":
                print(
                    "Player", players_here[connection].username, "finished a paragraph"
                )
                players_here[connection].text_pos += 1
                if players_here[connection].text_pos < 3:
                    update = {
                        "type": "newText",
                        "text": text[game_id][players_here[connection].text_pos],
                    }
                    connection.send(json.dumps(update))
                else:
                    # The player is done, calculate standings.
                    players_lost[game_id].append(connection)
                    players_here[connection].done = True
                    update_standings(game_id)

            elif data["type"] == "win":
                print(players_here[connection].username, "won!")
                players_won[game_id].append(connection)
                players_here[connection].done = True
                update_standings(game_id)

        except (KeyError, ConnectionError, ConnectionClosed):
            clients.remove(connection)
            players_here.pop(connection)

            if connection in players_won[game_id]:
                players_won[game_id].remove(connection)
            if connection in players_lost[game_id]:
                players_lost[game_id].remove(connection)

            break


def update_standings(game_id):
    standings = players_won[game_id] + players_lost[game_id]
    print(standings)
    players_here = players[game_id]
    players_here[standings[0]].standings = "1st"
    if len(standings) > 1:
        players_here[standings[1]].standings = "2nd"
    if len(standings) > 2:
        players_here[standings[2]].standings = "3rd"
    i = 4
    while i <= len(standings):
        players_here[standings[i - 1]].standings = str(i) + "th"

    if len(standings) == len(players_here):
        for client in players_here:
            client.send(json.dumps({"type": "gameOver"}))
