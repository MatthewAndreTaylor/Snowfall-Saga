from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

players = []


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('join_lobby')
def handle_join_lobby(data):
    username = data['username']
    players.append(username)
    emit('update_players', {'players': players}, broadcast=True)

    if len(players) == 4:
        emit('start_game', broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)
