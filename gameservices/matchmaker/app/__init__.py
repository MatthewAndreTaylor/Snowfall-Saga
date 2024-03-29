from flask import Flask, render_template, request, redirect
from flask_sock import Sock
from simple_websocket import ConnectionClosed, ConnectionError
from flask_login import LoginManager, UserMixin, current_user
import json
import random

app = Flask(__name__)
app.secret_key = "MYSECRET"

sock = Sock(app)

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(username):
    return User(username)

class User(UserMixin):
    def __init__(self, username):
        self.id = username

class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.users = {}
        self.hosts = {}
        self.clients = set()


game_rooms = {
    "trivia": RoomManager(),
    "blizzard_bounce": RoomManager(),
    "chess": RoomManager(),
    "type_race": RoomManager(),
}

character_set = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


class Room:
    def __init__(self, name, host):
        self.name = name
        self.host = host
        self.users = set()


def handle_load(connection, room_manager):
    rooms_data = []
    for room_name, room_obj in room_manager.rooms.items():
        rooms_data.append(
            {
                "name": room_name,
                "host": room_obj.host,
                "users": list(room_obj.users),
            }
        )

    response = {"type": "rooms", "rooms": rooms_data}
    connection.send(json.dumps(response))


def handle_create(connection, data, room_manager):
    user = data.get("user")
    if user in room_manager.hosts:
        connection.send(
            json.dumps(
                {
                    "type": "create",
                    "error": "You are already hosting a room",
                }
            )
        )
        return

    room_name = "".join(random.choices(character_set, k=6))
    room_manager.rooms[room_name] = Room(name=room_name, host=user)
    room_manager.hosts[user] = room_name
    response = {"type": "create", "room": room_name}

    client_response = {
        "type": "create",
        "room": room_name,
        "other": True,
    }
    for client in room_manager.clients:
        if client != connection:
            client.send(json.dumps(client_response))

    connection.send(json.dumps(response))


def handle_join(connection, data, room_manager):
    user = data.get("user")
    room_name = data.get("room")
    if room_name:
        room = room_manager.rooms.get(room_name)
        if room:
            if user not in room.users:
                for existing_room_name, existing_room in room_manager.rooms.items():
                    if user in existing_room.users:
                        if user == existing_room.host:
                            connection.send(
                                json.dumps(
                                    {
                                        "type": "leave",
                                        "error": "You are already hosting a room",
                                    }
                                )
                            )
                            return
                        existing_room.users.remove(user)

                        client_response = {
                            "type": "leave",
                            "room": existing_room_name,
                            "other": user,
                        }

                        for client in room_manager.clients:
                            if client != connection:
                                client.send(json.dumps(client_response))

                        connection.send(
                            json.dumps(
                                {
                                    "type": "leave",
                                    "room": existing_room_name,
                                }
                            )
                        )

                room.users.add(user)

                client_response = {
                    "type": "join",
                    "room": room_name,
                    "other": user,
                }
                for client in room_manager.clients:
                    if client != connection:
                        client.send(json.dumps(client_response))

                response = {"type": "join", "room": room_name}
                connection.send(json.dumps(response))
            else:
                connection.send(
                    json.dumps(
                        {
                            "type": "join",
                            "error": "You are already in this room",
                        }
                    )
                )
        else:
            connection.send(
                json.dumps(
                    {
                        "type": "join",
                        "error": f"Room {room_name} does not exist",
                    }
                )
            )


def handle_leave(connection, data, room_manager):
    user = data.get("user")
    room_name = data.get("room")
    if room_name:
        room = room_manager.rooms.get(room_name)
        if not room:
            return

        if user in room.users:
            if user == room.host:
                handle_delete({"room": room_name}, room_manager)
            else:
                room.users.remove(user)

            client_response = {
                "type": "leave",
                "room": room_name,
                "other": user,
            }

            for client in room_manager.clients:
                if client != connection:
                    client.send(json.dumps(client_response))

            connection.send(
                json.dumps(
                    {
                        "type": "leave",
                        "room": room_name,
                    }
                )
            )


def handle_delete(data, room_manager):
    room_name = data.get("room")
    if room_name:
        room = room_manager.rooms.get(room_name)
        if not room:
            return

        for user in room.users:
            user_response = {
                "type": "leave",
                "room": room_name,
            }
            room_manager.users[user].send(json.dumps(user_response))

        del room_manager.rooms[room_name]
        del room_manager.hosts[room.host]

        client_response = {
            "type": "delete",
            "room": room_name,
        }

        for client in room_manager.clients:
            client.send(json.dumps(client_response))


def handle_start(data, room_manager):
    room_name = data.get("room")
    user = data.get("user")
    if not user:
        return

    if room_name:
        room = room_manager.rooms.get(room_name)
        if not room:
            return

        if user != room.host:
            return

        handle_delete(data, room_manager)

        user_response = {"type": "start", "room": room_name}
        for user in room.users:
            room_manager.users[user].send(json.dumps(user_response))


@sock.route("/room_events/<string:game>")
def handle_matchmaking(connection, game: str):
    manager = game_rooms[game]

    if connection in manager.clients:
        return

    manager.clients.add(connection)

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            user = data.get("user")
            if user and user not in manager.users:
                manager.users[user] = connection
            elif not user:
                continue

            type = data.get("type")
            if not type:
                continue

            if type == "create":
                handle_create(connection, data, manager)
            elif type == "join":
                handle_join(connection, data, manager)
            elif type == "load":
                handle_load(connection, manager)
            elif type == "leave":
                handle_leave(connection, data, manager)
            elif type == "delete":
                handle_delete(data, manager)
            elif type == "start":
                handle_start(data, manager)

        except (KeyError, ConnectionError, ConnectionClosed):
            print("Lost matchmaking socket connection")
            manager.clients.remove(connection)
            break


game_service_hosts = {
  "blizzard_bounce": "127.0.0.1:8001",
  "trivia": "127.0.0.1:8002",
  "type_race": "127.0.0.1:8003",
  "chess": "127.0.0.1.:8004",
}

@app.route("/join/<string:game>/<string:game_id>", methods=["GET"])
def trivia(game: str, game_id: str):
    if game not in game_service_hosts:
        return "Invalid game", 404

    return redirect(f"http://{game_service_hosts[game]}/{game_id}")

@app.route("/matchmaking/<string:game>", methods=["GET"])
def index(game: str):
    return render_template("waiting_room.html", username=current_user.id, game=game)
