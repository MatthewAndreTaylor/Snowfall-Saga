from flask_socketio import SocketIO, join_room
from flask import request, session
from .questions import TriviaDB
import random
import requests


def trivia_game(socketio: SocketIO, users: dict, game_info: dict, db: TriviaDB):
    points = {}
    namespace = "/trivia/game/" + str(game_info["game_id"])

    def update_room_user_list():
        socketio.emit(
            "user_list",
            list(users.keys()),
            room=game_info["game_id"],
            namespace=namespace,
        )

    @socketio.on("connect", namespace=namespace)
    def connect():
        print("Client joined the game")
        socketio.emit("hi", namespace=namespace)
        join_room(game_info["game_id"])
        print(f"Users in room {game_info['game_id']}, {users.keys()}")
        socketio.emit(
            "user_list", list(users.keys()), room=request.sid, namespace=namespace
        )

    @socketio.on("disconnect", namespace=namespace)
    def disconnect():
        # Remove the user from users
        print(f"Users in room {game_info['game_id']}, {users.keys()}")
        if session.get("username") in users:
            users.pop(session.get("username"))
            update_room_user_list()

    @socketio.on("register", namespace=namespace)
    def register_user(username):
        session["username"] = username
        users[username] = request.sid
        points[username] = 0
        if len(points) == len(users):
            socketio.start_background_task(run_main_game)

    def run_main_game():
        question_number = 1
        while question_number <= game_info["num_questions"]:
            categories = db.get_categories()
            question = db.get_question_by_category(random.choice(categories))
            socketio.emit(
                "question", question, room=game_info["game_id"], namespace=namespace
            )

            answers = {}

            @socketio.on("answer", namespace=namespace)
            def receive_answer(answer):
                if session.get("username") in users:
                    print("Received answer from", session.get("username"))
                    answers[session.get("username")] = answer

            while len(answers) < len(users):
                socketio.sleep(1)

            print("Received answers", answers)
            for user in users:
                if answers[user] == question["correct"]:
                    points[user] += 10
                    socketio.emit(
                        "correct", points, room=users[user], namespace=namespace
                    )
                else:
                    socketio.emit(
                        "incorrect", points, room=users[user], namespace=namespace
                    )

            question_number += 1

        send_points(points)


def send_points(points):
    requests.post("http://127.0.0.1:5000/points", json=points)