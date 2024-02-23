from flask import Blueprint
from flask_sock import Sock
from flask_login import current_user, login_required
import json
from simple_websocket import ConnectionClosed
from .. import db
from ..models import User, Friendship

friendship = Blueprint(
    "friendship",
    __name__,
    template_folder="templates",
    static_folder="static",
)

sock = Sock(friendship)

clients = {}
users = {}


@sock.route("/send_friend_request")
@login_required
def friend_request(connection):
    send_friend_request(connection, from_user=current_user)


def send_friend_request(connection, from_user):
    if connection in clients:
        return

    clients[connection] = from_user.username
    users[from_user.username] = connection

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)
            to_user = data["username"]

            if to_user is None:
                connection.send({"error": "Username is required"})
                continue

            to_user = User.query.filter_by(username=to_user).first()

            if to_user is None:
                connection.send({"error": "User not found"})
            elif from_user == to_user:
                connection.send(
                    {"error": "You can't send a friend request to yourself"}
                )
            elif (
                Friendship.query.filter_by(
                    user_id=from_user.id, friend_id=to_user.id
                ).first()
                is not None
            ):
                connection.send({"error": "You are already friends"})
            elif (
                Friendship.query.filter_by(
                    user_id=to_user.id, friend_id=from_user.id
                ).first()
                is not None
            ):
                connection.send({"error": "You are already friends"})
            else:
                friendship = Friendship(
                    user_id=from_user.id, friend_id=to_user.id, status=0
                )
                db.session.add(friendship)
                db.session.commit()

                connection.send({"success": "Friend request sent"})

                users[to_user.username].send(
                    {
                        "type": "friend_request",
                        "from_user": from_user.username,
                        "to_user": to_user.username,
                    }
                )
        except (KeyError, ConnectionError, ConnectionClosed):
            user = clients[connection]
            del clients[connection]
            del users[user]
            print(f"Friendship Removed connection {connection}")
            break
