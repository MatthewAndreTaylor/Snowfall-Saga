from flask import Flask, render_template
from flask_sock import Sock
from simple_websocket import ConnectionClosed
import json
import os

template_dir = os.path.abspath(
    "/home/abhin/Documents/Snowfall-Saga/frontend/templates/"
)
app = Flask(__name__, template_folder=template_dir)
app.static_folder = "/home/abhin/Documents/Snowfall-Saga/frontend/templates/static/"
sock = Sock(app)

players = {}
clients = set()
connection_dict = {}


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")


@sock.route("/echo")
def echo(connection):
    if connection not in clients:
        clients.add(connection)
        print(f"Added connection {connection}")

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data["type"] == "playerUpdate":
                player_id = data["value"]["id"]
                if player_id not in players:
                    connection_dict[connection] = player_id
                players[player_id] = data["value"]
                send_to_all_clients({"type": "playersUpdate", "value": players})
            elif data["type"] == "playerRemoved":
                player_id = data["id"]
                del players[data["id"]]
                send_to_all_clients({"type": "playerRemoved", "id": player_id})

        except (ConnectionError, ConnectionClosed):
            clients.remove(connection)
            player_id = connection_dict[connection]
            send_to_all_clients({"type": "playerRemoved", "id": player_id})
            del connection_dict[connection]
            del players[player_id]
            print(f"Remove connection {connection}")
            break


def send_to_all_clients(message):
    for client in clients:
        client.send(json.dumps(message))


if __name__ == "__main__":
    app.run(debug=True)
