from app import app, socketio

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=9999)
