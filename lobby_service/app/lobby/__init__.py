from flask import Blueprint, render_template, redirect
from flask_login import current_user, login_required
from simple_websocket import ConnectionClosed
from flask_sock import Sock
from collections import deque
import json
from .. import db
from ..models import User

lobby_view = Blueprint(
    "lobby_view",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets/lobby",
)

sock = Sock(lobby_view)

# Store player information
players = {}

# Set of all client connections
clients = set()


@lobby_view.route("/")
@login_required
def lobby():
    return render_template("lobby/index.html", player_id=current_user.id)


@lobby_view.route("/matchmaking/<string:game>", methods=["GET"])
@login_required
def matchmaking(game: str):
    resp = redirect(f"http://127.0.0.1:5001/matchmaking/{game}")
    resp.set_cookie("Authorization", current_user.username)
    return resp


@sock.route("/echo")
def echo(connection):
    if connection in clients or current_user.id in players:
        return

    clients.add(connection)
    players[current_user.id] = {
        "name": current_user.username,
        "id": current_user.id,
        "sprite": current_user.sprite,
    }
    print(f"{current_user.username} joined with connection {connection}")

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data["type"] == "playerUpdate":
                # Update database with user's new sprite ONLY IF sprite changes
                if (
                    "sprite" in data["value"]
                    and data["value"]["sprite"] != current_user.sprite
                ):
                    current_user.sprite = data["value"]["sprite"]
                    db.session.commit()

                players[current_user.id].update(data["value"])
                send_to_all_clients({"type": "playersUpdate", "value": players})

            elif data["type"] == "playerRemoved":
                player_id = data["id"]
                if player_id in players:
                    del players[player_id]
                send_to_all_clients({"type": "playerRemoved", "id": player_id})

            elif data["type"] == "getSprites":
                message = {
                    "type": "getSprites",
                    "inventory": current_user.sprite_inventory,
                }
                connection.send(json.dumps(message))

            elif data["type"] == "throwSnowball":
                player_id = current_user.id
                destination_x = data["value"]["destinationX"]
                destination_y = data["value"]["destinationY"]

                throw_message = {
                    "type": "throwSnowball",
                    "value": {
                        "id": player_id,
                        "destinationX": destination_x,
                        "destinationY": destination_y,
                    },
                }
                send_to_all_clients(throw_message)

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
