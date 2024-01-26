from flask import Flask, render_template, request
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='../frontend/templates')
socketio = SocketIO(app)

users = {}

@app.route('/')
def index():
    return render_template('test/username.html')

@socketio.on('connect', namespace='/trivia')
def handle_connect():
    print('Client connected to /trivia:', request.sid)

@socketio.on('username', namespace='/trivia')
def get_username(username):
    users[request.sid] = username
    print('Received username', username)
    update_users()

@socketio.on('disconnect', namespace='/trivia')
def handle_disconnect():
    print('Client disconnected from /trivia:', request.sid)
    users.pop(request.sid)
    update_users()

def update_users():
    socketio.emit('user_list', list(users.values()), namespace='/trivia')

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)