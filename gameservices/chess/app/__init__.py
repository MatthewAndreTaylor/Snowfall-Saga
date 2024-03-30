import json
from collections import defaultdict
from flask import Flask, render_template, request
from flask_login import LoginManager, current_user, UserMixin
from flask_sock import Sock
from simple_websocket import ConnectionClosed
import chess

app = Flask(__name__)
app.secret_key = "MYSECRET"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
sock = Sock(app)
login_manager = LoginManager(app)

players_waiting = {}

players = defaultdict(list)
clients = set()
usernames = defaultdict(dict)


@login_manager.user_loader
def load_user(username):
    return User(username)


class User(UserMixin):
    def __init__(self, username: str):
        self.id = username


boards = {}
turns = {}


@app.route("/<string:game_id>", methods=["GET"])
def enter_chess(game_id: str):
    return render_template(
        "chess_waiting_room.html",
        username=current_user.id,
        gameId=game_id,
    )


@app.route("/chess/game/<string:game_id>", methods=["GET"])
def send_to_game(game_id: str):
    return render_template("chess_game.html", game_id=game_id)


@sock.route("/chess/<string:game_id>")
def waiting_room(connection, game_id: str):
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
                for client in clients:
                    client.send(json.dumps({"type": "switchPage", "url": "chess/game"}))

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


@sock.route("/chess/game/<game_id>")
def run_game(connection, game_id: str):
    if len(players[game_id]) == 0:
        boards[game_id] = chess.Board()
        turns[game_id] = 0

    players[game_id].append(connection)

    board = boards[game_id]

    print("got a connection")
    if connection in clients:
        return

    clients.add(connection)

    send_board(players[game_id], board)

    if len(players[game_id]) > 2:
        connection.send(
            json.dumps({"type": "message", "message": "You are spectating..."})
        )

    print(players)

    first_turn = True

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            print(players[game_id])

            if (
                turns[game_id] != -1
                and data["type"] == "makeMove"
                and len(players[game_id]) > 1
                and connection == players[game_id][turns[game_id]]
            ):
                if len(players[game_id]) > 1 and connection == players[game_id][1]:
                    move = chess.Move.from_uci(flip_move(data["move"]))
                    promote_move = chess.Move.from_uci(flip_move(data["move"]) + "q")
                else:
                    move = chess.Move.from_uci(data["move"])
                    promote_move = chess.Move.from_uci(data["move"] + "q")

                if move in board.legal_moves:
                    print(move)
                    board.push(move)
                    send_board(players[game_id], board)
                    turns[game_id] = change_turn(turns[game_id])
                    players[game_id][turns[game_id]].send(
                        json.dumps({"type": "yourTurn"})
                    )
                    if (not first_turn) or connection == players[game_id][1]:
                        players[game_id][1 - turns[game_id]].send(
                            json.dumps({"type": "notYourTurn"})
                        )
                    else:
                        first_turn = False
                    print("turn", turns[game_id])

                elif promote_move in board.legal_moves:
                    print(promote_move)
                    board.push(promote_move)
                    send_board(players[game_id], board)
                    turns[game_id] = change_turn(turns[game_id])
                    players[game_id][turns[game_id]].send(
                        json.dumps({"type": "yourTurn"})
                    )
                    if (not first_turn) or connection == players[game_id][1]:
                        players[game_id][1 - turns[game_id]].send(
                            json.dumps({"type": "notYourTurn"})
                        )
                    else:
                        first_turn = False
                    print("turn", turns[game_id])

                else:
                    connection.send(
                        json.dumps({"type": "message", "message": "Illegal Move!"})
                    )
                    print("Illegal move!")

                if board.is_game_over():
                    if board.is_checkmate():
                        if board.turn == chess.WHITE:
                            send_message(players[game_id], "Black wins by checkmate!")
                        else:
                            send_message(players[game_id], "White wins by checkmate!")
                    elif board.is_stalemate():
                        send_message(players[game_id], "Draw by stalemate.")
                    elif board.is_insufficient_material():
                        send_message(players[game_id], "Draw by insufficient material.")
                    elif board.is_seventyfive_moves():
                        send_message(players[game_id], "Draw by the 75-move rule.")
                    elif board.is_fivefold_repetition():
                        send_message(players[game_id], "Draw by fivefold repetition.")
                    else:
                        send_message(players[game_id], "Draw")
                    for player in players[game_id]:
                        if player is not None:
                            player.send(json.dumps({"type": "notYourTurn"}))

            elif (
                turns[game_id] != -1
                and data["type"] == "makeMove"
                and connection != players[game_id][turns[game_id]]
            ):
                connection.send(
                    json.dumps({"type": "message", "message": "It's not your turn!"})
                )
                print("Not your turn!")
                print(turns[game_id])

            elif data["type"] == "timeUp":
                if board.turn == chess.WHITE:
                    send_message(players[game_id], "Black wins by time!")
                else:
                    send_message(players[game_id], "White wins by time!")
                turns[game_id] = -1

            elif data["type"] == "username":
                usernames[game_id][connection] = data["username"]
                player1 = usernames[game_id][players[game_id][0]]
                if len(players[game_id]) > 1:
                    player2 = usernames[game_id][players[game_id][1]]
                else:
                    player2 = ""
                for player in players[game_id]:
                    if player is not None:
                        player.send(
                            json.dumps(
                                {
                                    "type": "usernames",
                                    "player1": player1,
                                    "player2": player2,
                                }
                            )
                        )

        except (KeyError, ConnectionError, ConnectionClosed):
            clients.remove(connection)
            for i in range(len(players[game_id])):
                if players[game_id][i] == connection:
                    players[game_id][i] = None
                    if i < 2:
                        for player in players[game_id]:
                            if player is not None:
                                player.send(
                                    json.dumps(
                                        {
                                            "type": "message",
                                            "message": "Player disconnected!",
                                        }
                                    )
                                )

            break


def send_board(players, board):
    for player in players:
        if player is not None:
            if len(players) > 1 and player == players[1]:
                flipped = flip_board(str(board))
                player.send(json.dumps({"type": "board", "board": flipped}))
            else:
                player.send(json.dumps({"type": "board", "board": str(board)}))


def send_message(players, message):
    for player in players:
        if player is not None:
            player.send(json.dumps({"type": "message", "message": message}))


def change_turn(turn):
    return 1 - turn


def flip_board(board_str):
    rows = board_str.strip().split("\n")
    reversed_rows = reversed(rows)
    flipped_board_str = "\n".join(reversed_rows)

    return flipped_board_str


def flip_move(move):
    start_col, start_row, end_col, end_row = move[0], move[1], move[2], move[3]
    flipped_start_row = start_col + str(8 - int(start_row) + 1)
    flipped_end_row = end_col + str(8 - int(end_row) + 1)
    return flipped_start_row + flipped_end_row
