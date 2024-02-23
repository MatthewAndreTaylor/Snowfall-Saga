from flask import Blueprint, render_template, redirect, send_from_directory
from flask_login import current_user, login_required
from simple_websocket import ConnectionClosed
from flask_sock import Sock
import requests
from collections import deque
import json
import os

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

# Previous messages before the player spawned are saved
message_cache = deque(maxlen=6)


@lobby_view.route("/audio/<filename>")
def audio(filename):
    return send_from_directory(
        os.path.join(lobby_view.root_path, "static", "audio"), filename
    )


@lobby_view.route("/")
@login_required
def lobby():
    return render_template("lobby/index.html", player_id=current_user.id)


@lobby_view.route("/trivia", methods=["GET"])
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
