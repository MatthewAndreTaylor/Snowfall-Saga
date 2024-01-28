from flask import Flask, render_template, request
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='../frontend/templates')
socketio = SocketIO(app)

users = {}
user_queue = []
num_questions = [10]
timer = [10]


@app.route('/')
def index():
    return render_template('test/username.html')


@socketio.on('connect', namespace='/trivia')
def handle_connect():
    print('Client connected to /trivia:', request.sid)


@socketio.on('username', namespace='/trivia')
def get_username(username):
    users[request.sid] = username
    user_queue.append(request.sid)
    print('Received username', username)
    update_users()
    socketio.emit('num_questions', num_questions[0], namespace='/trivia', room=request.sid)
    socketio.emit('timer', timer[0], namespace='/trivia', room=request.sid)
    if len(users) == 1:
        update_party_leader()


@socketio.on('disconnect', namespace='/trivia')
def handle_disconnect():
    print('Client disconnected from /trivia:', request.sid)
    users.pop(request.sid)
    user_queue.remove(request.sid)
    update_users()
    update_party_leader()


@socketio.on('num_questions', namespace='/trivia')
def update_num_questions(new_num):
    num_questions[0] = new_num
    socketio.emit('num_questions', num_questions[0], namespace='/trivia')


@socketio.on('timer', namespace='/trivia')
def update_timer(new_timer):
    timer[0] = int(new_timer)
    socketio.emit('timer', timer[0], namespace='/trivia')


def update_users():
    socketio.emit('user_list', list(users.values()), namespace='/trivia')


def update_party_leader():
    if len(user_queue) > 0:
        socketio.emit('party_leader', room=user_queue[0], namespace='/trivia')


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)