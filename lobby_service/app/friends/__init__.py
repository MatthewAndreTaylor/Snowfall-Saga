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
    static_url_path="/assets/friends",
)

sock = Sock(friendship)
users = {}
clients = set()


def myFriendRequests() -> list:
    pending = Friendship.query.filter_by(friend_id=current_user.id, status=0).all()
    friend_requests = [
        User.query.filter_by(id=request.user_id).first().username for request in pending
    ]
    return friend_requests


def queryFriends(user: User) -> list:
    friends = Friendship.query.filter_by(user_id=user.id, status=1).all()
    friends2 = Friendship.query.filter_by(friend_id=user.id, status=1).all()
    friend_list = []

    for friend in friends:
        user0 = User.query.filter_by(id=friend.friend_id).first()
        friend_list.append(user0.username)
    for friend in friends2:
        user1 = User.query.filter_by(id=friend.user_id).first()
        friend_list.append(user1.username)
    return friend_list


@sock.route("/friends")
@login_required
def friends(connection):
    if connection in clients:
        return

    clients.add(connection)
    users[current_user.username] = connection

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data["type"] == "getFriends":
                friend_list = queryFriends(current_user)
                # print(current_user.username, "checked out friendlist", friend_list)
                connection.send(json.dumps({"type": "friends", "friends": friend_list}))

            if data["type"] == "getFriendRequests":
                friend_requests = myFriendRequests()
                # print(current_user.username, "checked out friend requests", friend_requests)
                connection.send(
                    json.dumps({"type": "friend_requests", "requests": friend_requests})
                )

            if data["type"] == "sendFriendRequest":
                to_user = User.query.filter_by(username=data["username"]).first()
                if to_user is None:
                    message = {"error": "User not found", "type": "sent_friend_request"}
                    connection.send(json.dumps(message))
                    continue
                if to_user == current_user:
                    message = {
                        "error": "You can't send a friend request to yourself",
                        "type": "sent_friend_request",
                    }
                    connection.send(json.dumps(message))
                    continue

                friendship = Friendship.query.filter_by(
                    user_id=current_user.id, friend_id=to_user.id
                ).first()
                friendship2 = Friendship.query.filter_by(
                    user_id=to_user.id, friend_id=current_user.id
                ).first()

                message = None
                if friendship is not None:
                    if friendship.status == 0:
                        message = {"error": "Friend request already sent to you"}
                    elif friendship.status == 1:
                        message = {"error": "You are already friends"}
                    elif friendship2 is None or friendship2.status == 2:
                        friendship.status = 0
                        db.session.commit()
                        message = {"success": "Friend request sent"}

                if message is None and friendship2 is not None:
                    if friendship2.status == 0:
                        message = {"error": "Friend request already sent to you"}
                    elif friendship2.status == 1:
                        message = {"error": "You are already friends"}
                if message is None:
                    friendship = Friendship(
                        user_id=current_user.id, friend_id=to_user.id, status=0
                    )
                    db.session.add(friendship)
                    db.session.commit()
                    message = {"success": "Friend request sent"}

                # print(current_user.username, " sent friend request to ", to_user.username, " message: ", message)
                message = {**message, "type": "sent_friend_request"}
                connection.send(json.dumps(message))

            if data["type"] == "acceptFriendRequest":
                user = User.query.filter_by(username=data["username"]).first()
                if user is None:
                    message = {"error": "User not found"}
                    connection.send(json.dumps(message))
                    continue
                friendship = Friendship.query.filter_by(
                    user_id=user.id, friend_id=current_user.id, status=0
                ).first()
                if friendship is None:
                    message = {"error": "Friend request not found"}
                    connection.send(json.dumps(message))
                    continue
                friendship.status = 1
                db.session.commit()
                message = {
                    "success": "Friend request accepted",
                    "username": data["username"],
                }
                # print(current_user.username, " accepted friend request from ", user.username, " message: ", message)

                # Update the accepting user's requests list
                connection.send(
                    json.dumps(
                        {"type": "friend_requests", "requests": myFriendRequests()}
                    )
                )

                # Signal the two users that thier friendship has been accepted
                connection.send(
                    json.dumps(
                        {"type": "friends", "friends": queryFriends(current_user)}
                    )
                )
                users[user.username].send(
                    json.dumps({"type": "friends", "friends": queryFriends(user)})
                )

            if data["type"] == "rejectFriendRequest":
                sent_from = data["username"]
                user = User.query.filter_by(username=sent_from).first()
                if user is None:
                    message = {"error": "User not found"}
                    connection.send(json.dumps(message))
                    continue
                friendship = Friendship.query.filter_by(
                    user_id=user.id, friend_id=current_user.id, status=0
                ).first()
                if friendship is None:
                    message = {"error": "Friend request not found"}
                    connection.send(json.dumps(message))
                    continue
                friendship.status = 2
                db.session.commit()
                message = {"success": "Friend request rejected", "username": sent_from}
                # print(current_user.username, " rejected friend request from ", user.username, " message: ", message)
                connection.send(json.dumps(message))

            # Update the rejecting user's requests list
            connection.send(
                json.dumps({"type": "friend_requests", "requests": myFriendRequests()})
            )

        except (KeyError, ConnectionError, ConnectionClosed):
            print("Lost friend socket connection", current_user.username)
            clients.remove(connection)
            del users[connection]
            break
