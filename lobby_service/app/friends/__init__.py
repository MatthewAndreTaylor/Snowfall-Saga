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


@sock.route("/get_friends")
@login_required
def get_friends(connection):
    if connection in clients:
        return

    clients[connection] = current_user.username
    users[current_user.username] = connection

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)
            type = data["type"]
            if type == "getFriends":
                message = getAllFriends(current_user.username)
                connection.send(json.dumps(message))
                if data["sent_from"] != "":
                    from_user = data["sent_from"]
                    if from_user in users:
                        message = getAllFriends(from_user)
                        users[from_user].send(json.dumps(message))
        except (KeyError, ConnectionError, ConnectionClosed):
            user = clients[connection]
            del clients[connection]
            del users[user]
            break


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


@sock.route("/accept_friend_request")
@login_required
def accept_friend_request(connection):
    from_user = current_user
    while True:
        try:
            event = connection.receive()
            data = json.loads(event)
            type = data["type"]
            if type == "acceptFriendRequest":
                sent_from = data["username"]
                if sent_from is None:
                    connection.send(
                        json.dumps({"error": "Error accepting friend request"})
                    )
                    continue
                user = User.query.filter_by(username=sent_from).first()
                if user is None:
                    message = {"error": "User not found"}
                    connection.send(json.dumps(message))
                    continue
                friendship = Friendship.query.filter_by(
                    user_id=user.id, friend_id=from_user.id, status=0
                ).first()
                if friendship is None:
                    message = {"error": "Friend request not found"}
                    connection.send(json.dumps(message))
                    continue
                friendship.status = 1
                db.session.commit()
                message = {
                    "success": "Friend request accepted",
                    "username": sent_from,
                }
                connection.send(json.dumps(message))
        except (KeyError, ConnectionError, ConnectionClosed):
            break


@sock.route("/reject_friend_request")
@login_required
def reject_friend_request(connection):
    from_user = current_user
    while True:
        try:
            event = connection.receive()
            data = json.loads(event)
            type = data["type"]
            if type == "rejectFriendRequest":
                sent_from = data["username"]
                if sent_from is None:
                    connection.send(
                        json.dumps({"error": "Error rejecting friend request"})
                    )
                    continue
                user = User.query.filter_by(username=sent_from).first()
                if user is None:
                    message = {"error": "User not found"}
                    connection.send(json.dumps(message))
                    continue
                friendship = Friendship.query.filter_by(
                    user_id=user.id, friend_id=from_user.id, status=0
                ).first()
                if friendship is None:
                    message = {"error": "Friend request not found"}
                    connection.send(json.dumps(message))
                    continue
                friendship.status = 2
                db.session.commit()
                message = {
                    "success": "Friend request rejected",
                    "username": sent_from,
                }
                connection.send(json.dumps(message))
        except (KeyError, ConnectionError, ConnectionClosed):
            break


def send_friend_request(connection, from_user):
    if connection in clients:
        return

    clients[connection] = from_user.username
    users[from_user.username] = connection

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            type = data["type"]
            if type != "friendRequest":
                continue

            to_user = data["username"]
            if to_user is None:
                connection.send(json.dumps({"error": "Error sending friend request"}))
                continue

            to_user = User.query.filter_by(username=to_user).first()

            if to_user is None:
                message = {"error": "User not found"}
                connection.send(json.dumps(message))
                continue
            elif from_user == to_user:
                message = {
                    "error": "You can't send a friend request to yourself",
                }
                connection.send(json.dumps(message))
                continue

            friendship = Friendship.query.filter_by(
                user_id=from_user.id, friend_id=to_user.id
            ).first()
            friendship2 = Friendship.query.filter_by(
                user_id=to_user.id, friend_id=from_user.id
            ).first()

            message = None

            if friendship is not None:
                if friendship.status == 0:
                    message = {
                        "error": "Friend request already sent",
                    }
                elif friendship.status == 1:
                    message = {
                        "error": "You are already friends",
                    }
                elif friendship2 is None or friendship2.status == 2:
                    friendship.status = 0
                    db.session.commit()
                    message = {"success": "Friend request sent"}

            if message is None and friendship2 is not None:
                if friendship2.status == 0:
                    message = {
                        "error": "Friend request already sent to you",
                    }
                elif friendship2.status == 1:
                    message = {
                        "error": "You are already friends",
                    }

            if message is None:
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


def getAllFriends(curr_user):
    curr_user = User.query.filter_by(username=curr_user).first()
    if curr_user is None:
        return {"error": "User not found"}

    friends = Friendship.query.filter_by(user_id=curr_user.id, status=1).all()
    friends2 = Friendship.query.filter_by(friend_id=curr_user.id, status=1).all()

    friend_list = []

    for friend in friends:
        user = User.query.filter_by(id=friend.friend_id).first()
        friend_list.append({"username": user.username})
    for friend in friends2:
        user = User.query.filter_by(id=friend.user_id).first()
        friend_list.append({"username": user.username})

    message = {
        "type": "friends",
        "friends": friend_list,
    }
    return message
