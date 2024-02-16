from datetime import datetime
from flask import Blueprint
from flask_login import current_user
from simple_websocket import ConnectionClosed
from flask_sock import Sock
from collections import deque, defaultdict
from functools import partial
import json
from ..models import User

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

    # Sort the messages by time
    missed_mesages = sorted(
        message_caches["all"] + message_caches[current_user.username],
        key=lambda message: message["time"],
    )

    # Send the last few messages a player missed before they spawned
    for message in missed_mesages:
        connection.send(json.dumps(message))

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            new_message = {
                "type": data["type"],
                "text": data["text"],
                "id": current_user.id,
                "name": current_user.username,
                "time": datetime.now().isoformat(),
            }

            if data["type"] == "newMessage":
                message_caches["all"].append(new_message)
                send_to_all_clients(new_message)

            elif data["type"] == "directMessage":
                to = data["to"]
                if connection != users.get(to):
                    # Show on both your screen and the other person
                    connection.send(json.dumps(new_message))

                if to in users or User.query.filter_by(username=to).first():
                    message_caches[to].append(new_message)

                if to in users:
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
