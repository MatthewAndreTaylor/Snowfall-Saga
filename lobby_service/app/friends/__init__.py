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


@sock.route("/get_friend_requests")
@login_required
def get_friend_requests(connection):
    while True:
        try:
            event = connection.receive()
            data = json.loads(event)
            type = data["type"]
            if type == "getFriendRequests":
                pending_requests = Friendship.query.filter_by(
                    friend_id=current_user.id, status=0
                ).all()

                friend_requests = []
                for request in pending_requests:
                    user = User.query.filter_by(id=request.user_id).first()
                    friend_requests.append(
                        {
                            "from_user": user.username,
                        }
                    )
                message = {
                    "type": "friend_requests",
                    "requests": friend_requests,
                }
                connection.send(json.dumps(message))
        except (KeyError, ConnectionError, ConnectionClosed):
            break


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
                connection.send(json.dumps({"error": "Error sending friend request"}))
                continue

            to_user = User.query.filter_by(username=to_user).first()

            if to_user is None:
                message = {"error": "User not found"}
            elif from_user == to_user:
                message = {
                    "error": "You can't send a friend request to yourself",
                }
            elif (
                Friendship.query.filter_by(
                    user_id=from_user.id, friend_id=to_user.id
                ).first()
                is not None
            ):
                message = {"error": "You are already friends"}
            elif (
                Friendship.query.filter_by(
                    user_id=to_user.id, friend_id=from_user.id
                ).first()
                is not None
            ):
                message = {"error": "You are already friends"}
            else:
                friendship = Friendship(
                    user_id=from_user.id, friend_id=to_user.id, status=0
                )
                db.session.add(friendship)
                db.session.commit()

                message = {"success": "Friend request sent"}

            connection.send(json.dumps(message))

        except (KeyError, ConnectionError, ConnectionClosed):
            user = clients[connection]
            del clients[connection]
            del users[user]
            print(f"Friendship Removed connection {connection}")
            break
