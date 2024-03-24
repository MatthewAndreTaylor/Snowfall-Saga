from flask import Flask, render_template, request
from flask_sock import Sock
import json
from simple_websocket import ConnectionClosed, ConnectionError

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

sock = Sock(app)

rooms, users, hosts, clients = {}, {}, {}, set()
current_user = {"username": "Guest"}


class Room:
    def __init__(self, name, host):
        self.name = name
        self.host = host
        self.users = set()


@sock.route("/load_rooms")
def load_rooms(connection):
    if connection in clients:
        return

    clients.add(connection)

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data.get("user"):
                users[data["user"]] = connection
            else:
                continue

            if data.get("type") and data["type"] == "load":
                response = {"type": "rooms", "rooms": list(rooms.keys())}
                connection.send(json.dumps(response))

        except (KeyError, ConnectionError, ConnectionClosed):
            print("Lost loading rooms socket connection")
            clients.remove(connection)
            break


@sock.route("/create_room")
def create_room(connection):
    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            user = data.get("user")
            if user and user not in users:
                users[user] = connection
            elif not user:
                continue

            if user in hosts:
                connection.send(
                    json.dumps(
                        {
                            "type": "create",
                            "error": "You are already hosting a room",
                        }
                    )
                )
                continue

            room_name = data.get("room")
            if room_name:
                if room_name in rooms:
                    response = {
                        "type": "create",
                        "error": f"Room {room_name} already exists",
                    }
                else:
                    rooms[room_name] = Room(name=room_name, host=user)
                    hosts[user] = room_name
                    response = {"type": "create", "room": room_name}

                    client_response = {
                        "type": "room",
                        "room": room_name,
                        "other": True,
                    }
                    for client in clients:
                        client.send(json.dumps(client_response))

                connection.send(json.dumps(response))
        except (KeyError, ConnectionError, ConnectionClosed):
            print("Lost creating room socket connection")
            break


@sock.route("/join_room")
def join_room(connection):
    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            user = data.get("user")
            if user and user not in users:
                users[user] = connection
            elif not user:
                continue

            room_name = data.get("room")
            if room_name:
                room = rooms.get(room_name)
                if room:
                    if user not in room.users:
                        room.users.add(user)

                        client_response = {
                            "type": "join",
                            "room": room_name,
                            "other": user,
                        }
                        for client in clients:
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

        except (KeyError, ConnectionError, ConnectionClosed):
            print("Lost joining room socket connection")
            break


@app.route("/matchmaking", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        current_user["username"] = request.json["username"]
    return render_template("waiting_room.html", username=current_user["username"])
