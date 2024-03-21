import json
import random
from collections import defaultdict

from flask import Flask, Blueprint, render_template, request
from flask_sock import Sock
from simple_websocket import ConnectionClosed

import chess

chess_game = Blueprint(
    "chess_game",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets/chess",
)

sock = Sock(chess_game)

players = {}
clients = set()


current_user = {"username": "JOE", "game_id": 0}

boards = []


def create_chess_app():
    app = Flask(__name__)
    app.secret_key = "MYSECRET"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    with app.app_context():
        app.register_blueprint(chess_game)

    boards.append(chess.Board())
    print(str(boards[0]))

    return app


@chess_game.route("/chess", methods=["GET", "POST"])
def type_race():
    if request.method == "POST":
        print("Got HERE")
        current_user["username"] = request.json["username"]
    else:
        current_user["username"] = "JOE" + str(random.randint(1, 10000))
    return render_template(
        "chess_game.html",
        username=current_user["username"],
        gameId=current_user["game_id"],
    )


@sock.route("/chess")
def run_game(connection):
    board = boards[0]
    print("got a connection")
    if connection in clients:
        return

    clients.add(connection)

    send_board(clients, board)

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data['type'] == 'makeMove':
                move = chess.Move.from_uci(data['move'])
                if move in board.legal_moves:
                    print(move)
                    board.push(move)
                    send_board(clients, board)
                else:
                    print('Illegal move!')

                if board.is_checkmate():
                    print('The game is over!')

        except (KeyError, ConnectionError, ConnectionClosed):
            clients.remove(connection)

            break


def send_board(players, board):
    for player in players:
        player.send(json.dumps({'type': 'board', 'board': str(board)}))

