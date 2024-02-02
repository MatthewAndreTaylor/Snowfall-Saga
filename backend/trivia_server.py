from flask import Flask, render_template, request, session
from flask_socketio import SocketIO
from trivia_game_server import trivia_game

app = Flask(__name__, template_folder='../frontend/templates')
socketio = SocketIO(app)

users = {}
user_queue = []
game_info = {'num_questions': 10, 'timer': 10, 'game_id': 0}


@app.route('/')
def index():
    return render_template('test/username.html')


@app.route('/trivia/game')
def render_game():
    return render_template('test/testgame.html', game_id=game_info['game_id'])


@socketio.on('connect', namespace='/trivia')
def handle_connect():
    print('Client connected to /trivia:', request.sid)


@socketio.on('start_game', namespace='/trivia')
def start_game():
    print('Starting the game')
    # socketio.emit('switch_page',  game_info, namespace='/trivia')
    game_info['game_id'] += 1
    socketio.start_background_task(trivia_game(socketio, users.copy(), game_info.copy()))
    socketio.emit('switch_page', {'url': 'trivia/game'}, namespace='/trivia')


@socketio.on('username', namespace='/trivia')
def get_username(username):
    session['username'] = username
    users[username] = request.sid
    user_queue.append(request.sid)
    print('Received username', username)
    update_users()
    socketio.emit('num_questions', game_info['num_questions'], namespace='/trivia', room=request.sid)
    socketio.emit('timer', game_info['timer'], namespace='/trivia', room=request.sid)
    if len(users) == 1:
        update_party_leader()


@socketio.on('disconnect', namespace='/trivia')
def handle_disconnect():
    if session.get('username') in users:
        print('Client disconnected from /trivia:', request.sid)
        users.pop(session.get('username'))
        user_queue.remove(request.sid)
        update_users()
        update_party_leader()


@socketio.on('num_questions', namespace='/trivia')
def update_num_questions(new_num):
    game_info['num_questions'] = new_num
    socketio.emit('num_questions', game_info['num_questions'], namespace='/trivia')


@socketio.on('timer', namespace='/trivia')
def update_timer(new_timer):
    game_info['timer'] = int(new_timer)
    socketio.emit('timer', game_info['timer'], namespace='/trivia')


def update_users():
    socketio.emit('user_list', list(users.keys()), namespace='/trivia')


def update_party_leader():
    if len(user_queue) > 0:
        socketio.emit('party_leader', room=user_queue[0], namespace='/trivia')


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
