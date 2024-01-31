from flask_socketio import SocketIO, join_room
from flask import request, session


def trivia_game(socketio: SocketIO, users: dict, game_info: dict):

    @socketio.on('connect', namespace='/trivia/game')
    def connect():
        print('Client joined the game')
        socketio.emit('hi', namespace='/trivia/game')
        join_room(game_info['game_id'])
        print(f"Users in room {game_info['game_id']}, {users.keys()}")
        socketio.emit('user_list', list(users.keys()), room=request.sid, namespace='/trivia/game')

    @socketio.on('disconnect', namespace='/trivia/game')
    def disconnect():
        # Remove the user from users
        print(f"Users in room {game_info['game_id']}, {users.keys()}")
        if session.get('username') in users:
            users.pop(session.get('username'))
            update_room_user_list()

    @socketio.on('register', namespace='/trivia/game')
    def register_user(username):
        session['username'] = username

    def update_room_user_list():
        socketio.emit('user_list', list(users.keys()), room=game_info['game_id'], namespace='/trivia/game')
