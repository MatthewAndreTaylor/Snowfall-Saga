from flask import Blueprint
from flask_sock import Sock
from flask_login import current_user, login_required
from flask import jsonify
import json
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
    event = connection.receive()
    data = json.loads(event)
    username = data["username"]
    if username is None:
        return jsonify({"error": "Username not provided"}), 400
    send_friend_request(connection, from_user=current_user, to_user=username)


def send_friend_request(connection, from_user, to_user):
    if connection in clients:
        return

    clients[connection] = from_user.username
    users[from_user.username] = connection

    to_user = User.query.filter_by(username=to_user).first()
    if to_user is None:
        return jsonify({"error": "User not found"}), 404

    if from_user == to_user:
        return jsonify({"error": "You cannot add yourself as a friend"}), 400

    if (
        Friendship.query.filter_by(user_id=from_user.id, friend_id=to_user.id).first()
        is not None
    ):
        return jsonify({"error": "You are already friends"}), 400

    if (
        Friendship.query.filter_by(user_id=to_user.id, friend_id=from_user.id).first()
        is not None
    ):
        return jsonify({"error": "You are already friends"}), 400

    friendship = Friendship(user_id=from_user.id, friend_id=to_user.id, status=0)
    db.session.add(friendship)
    db.session.commit()

    users[to_user.username].send(
        {
            "type": "friend_request",
            "from_user": from_user.username,
            "to_user": to_user.username,
        }
    )
