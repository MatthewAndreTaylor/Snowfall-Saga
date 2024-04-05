from datetime import datetime
from flask import Blueprint
from flask_login import current_user, login_required
from simple_websocket import ConnectionClosed
from flask_sock import Sock
from collections import deque, defaultdict
from functools import partial
import json
from ..models import User
from ..badwords import words

from better_profanity import profanity

profanity.load_censor_words(words)

messenger = Blueprint(
    "messenger",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets/messages",
)

sock = Sock(messenger)

# Previous messages before the player spawned are saved
message_caches = defaultdict(partial(deque, maxlen=3))

# Mapping of connections to current user id's
clients = {}
users = {}


@sock.route("/message")
@login_required
def message(connection):
    send_message(connection, curr_user=current_user)


def send_message(connection, curr_user):
    if connection in clients:
        return

    # In the case of a test, the current user does not exist
    if curr_user is None:
        curr_user = User()
        curr_user.username = "TestUser"
        curr_user.id = 1

    clients[connection] = curr_user.username
    users[curr_user.username] = connection

    # Sort the messages by time
    missed_mesages = sorted(
        message_caches["all"] + message_caches[curr_user.username],
        key=lambda message: message["time"],
    )

    # Send the last few messages a player missed before they spawned
    for message in missed_mesages:
        connection.send(json.dumps(message))

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            message_type = data.get("type", "")
            message_content = data.get("text", "")
            if profanity.contains_profanity(message_content):
                message_content = len(message_content) * "*"

            # Create a new message object
            new_message = {
                "type": message_type,
                "text": message_content,
                "id": curr_user.id,
                "name": curr_user.username,
                "time": datetime.now().isoformat(),
            }

            if message_type == "newMessage":
                message_caches["all"].append(new_message)
                send_to_all_clients(new_message)

            elif message_type == "directMessage":
                to = data.get("to", connection)
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
