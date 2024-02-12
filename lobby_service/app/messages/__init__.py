from flask import Blueprint
from flask_login import current_user
from simple_websocket import ConnectionClosed
from flask_sock import Sock
from collections import deque, defaultdict
from functools import partial
import json

messenger = Blueprint(
    "messenger",
    __name__,
    template_folder="templates",
    static_folder="static",
)

sock = Sock(messenger)

# Previous messages before the player spawned are saved
message_caches = defaultdict(partial(deque, maxlen=3))

# Mapping of connections to current user id's
clients = {}
users = {}


@sock.route("/message")
def message(connection):
    if connection in clients:
        return

    clients[connection] = current_user.username
    users[current_user.username] = connection

    # Send the last few messages a player missed before they spawned
    for message in message_caches["all"]:
        connection.send(json.dumps(message))
    for message in message_caches[current_user.username]:
        connection.send(json.dumps(message))

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data["type"] == "newMessage":
                text = data["text"]

                new_message = {
                    "type": "newMessage",
                    "text": text,
                    "id": current_user.id,
                    "name": current_user.username,
                }
                message_caches["all"].append(new_message)
                send_to_all_clients(new_message)
            elif data["type"] == "directMessage":
                to = data["to"]
                text = data["text"]

                new_message = {
                    "type": "directMessage",
                    "text": text,
                    "id": current_user.id,
                    "name": current_user.username,
                }
                if connection != users.get(to):
                    connection.send(json.dumps(new_message))

                if to in users:
                    message_caches[to].append(new_message)
                    # Show on both your screen and the other person
                    users[to].send(json.dumps(new_message))

        except (KeyError, ConnectionError, ConnectionClosed):
            user = clients[connection]
            del clients[connection]
            del users[user]
            print(f"Messenger Removed connection {connection}")
            break


def send_to_all_clients(message: dict):
    """Sends a message to all connected clients.

    Args:
        message (dict): The message to be sent.
    """
    for client in clients:
        client.send(json.dumps(message))
