from flask import Flask, render_template
from flask_sock import Sock
from simple_websocket import ConnectionClosed
import json

app = Flask(__name__)
sock = Sock(app)

players = {}
clients = set()
connection_dict = {}
messages = []
usernames = []


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
                if data.get('oldname'):
                    usernames.remove((data['oldname'], player_id))
                usernames.append((data['value']['name'], player_id))
                players[player_id] = data["value"]
                send_to_all_clients({"type": "playersUpdate", "value": players, "id": player_id})
            elif data["type"] == "playerRemoved":
                player_id = data["id"]
                usernames.remove((data['name'], player_id))
                del players[data["id"]]
                send_to_all_clients({"type": "playerRemoved", "id": player_id})
            elif data['type'] == 'newMessage':
                message = f"{data.get('sender')}: {data.get('data')}"
                print(message)
                messages.append(message)
                send_to_all_clients({'type': 'newMessage', 'message': message, 'id': data['id']})
            elif data['type'] == 'timeoutMessage':
                player_id = data['id']
                send_to_all_clients({'type': 'timeoutMessage', 'id': player_id})

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
