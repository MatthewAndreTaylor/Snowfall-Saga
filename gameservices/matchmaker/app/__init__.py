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


def handle_load(connection):
    rooms_data = []
    for room_name, room_obj in rooms.items():
        rooms_data.append(
            {
                "name": room_name,
                "host": room_obj.host,
                "users": list(room_obj.users),
            }
        )

    response = {"type": "rooms", "rooms": rooms_data}
    connection.send(json.dumps(response))


def handle_create(connection, data):
    user = data.get("user")
    if user in hosts:
        connection.send(
            json.dumps(
                {
                    "type": "create",
                    "error": "You are already hosting a room",
                }
            )
        )
        return

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
                "type": "create",
                "room": room_name,
                "other": True,
            }
            for client in clients:
                if client != connection:
                    client.send(json.dumps(client_response))

        connection.send(json.dumps(response))


def handle_join(connection, data):
    user = data.get("user")
    room_name = data.get("room")
    if room_name:
        room = rooms.get(room_name)
        if room:
            if user not in room.users:
                for existing_room_name, existing_room in rooms.items():
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

                        for client in clients:
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
                for client in clients:
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


def handle_leave(connection, data):
    user = data.get("user")
    room_name = data.get("room")
    if room_name:
        room = rooms.get(room_name)
        if not room:
            return

        if user in room.users:
            if user == room.host:
                connection.send(
                    json.dumps(
                        {
                            "type": "leave",
                            "error": "You cannot leave a room you are hosting",
                        }
                    )
                )
                return

            room.users.remove(user)

            client_response = {
                "type": "leave",
                "room": room_name,
                "other": user,
            }

            for client in clients:
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


@sock.route("/room_events")
def handle_matchmaking(connection):
    if connection in clients:
        return

    clients.add(connection)

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            user = data.get("user")
            if user and user not in users:
                users[user] = connection
            elif not user:
                continue

            type = data.get("type")
            if not type:
                continue

            if type == "create":
                handle_create(connection, data)
            elif type == "join":
                handle_join(connection, data)
            elif type == "load":
                handle_load(connection)
            elif type == "leave":
                handle_leave(connection, data)

        except (KeyError, ConnectionError, ConnectionClosed):
            print("Lost matchmaking socket connection")
            clients.remove(connection)
            break


@app.route("/matchmaking", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        current_user["username"] = request.json["username"]
    return render_template("waiting_room.html", username=current_user["username"])
