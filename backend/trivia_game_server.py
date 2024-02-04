from flask_socketio import SocketIO, join_room
from flask import request, session
import random


def trivia_game(socketio: SocketIO, users: dict, game_info: dict):
    points = {}
    namespace = f"/trivia/game/{game_info['game_id']}"
    answers = {}
    trivia_questions = [
        {'question': 'What is the capital of France?', 'option1': 'Berlin', 'option2': 'Madrid', 'option3': 'Rome',
         'option4': 'Paris', 'correct': 'option4'},
        {'question': 'Which planet is known as the Red Planet?', 'option1': 'Earth', 'option2': 'Mars',
         'option3': 'Venus', 'option4': 'Jupiter', 'correct': 'option2'},
        {'question': 'In what year did World War II end?', 'option1': '1939', 'option2': '1941', 'option3': '1945',
         'option4': '1950', 'correct': 'option3'},
        {'question': 'Who wrote "Romeo and Juliet"?', 'option1': 'Charles Dickens', 'option2': 'William Shakespeare',
         'option3': 'Jane Austen', 'option4': 'Mark Twain', 'correct': 'option2'},
        {'question': 'What is the largest mammal in the world?', 'option1': 'Elephant', 'option2': 'Blue Whale',
         'option3': 'Giraffe', 'option4': 'Hippopotamus', 'correct': 'option2'},
        {'question': 'Which programming language is known for its readability and simplicity?', 'option1': 'Java',
         'option2': 'Python', 'option3': 'C++', 'option4': 'Ruby', 'correct': 'option2'},
        {'question': 'Who painted the Mona Lisa?', 'option1': 'Vincent van Gogh', 'option2': 'Pablo Picasso',
         'option3': 'Leonardo da Vinci', 'option4': 'Claude Monet', 'correct': 'option3'},
        {'question': 'What is the capital of Japan?', 'option1': 'Seoul', 'option2': 'Beijing', 'option3': 'Tokyo',
         'option4': 'Bangkok', 'correct': 'option3'},
        {'question': 'Which ocean is the largest?', 'option1': 'Atlantic Ocean', 'option2': 'Indian Ocean',
         'option3': 'Southern Ocean', 'option4': 'Pacific Ocean', 'correct': 'option4'},
        {'question': 'Who developed the theory of relativity?', 'option1': 'Isaac Newton', 'option2': 'Galileo Galilei',
         'option3': 'Albert Einstein', 'option4': 'Niels Bohr', 'correct': 'option3'},
        {'question': 'What is the capital of Australia?', 'option1': 'Sydney', 'option2': 'Melbourne',
         'option3': 'Canberra', 'option4': 'Perth', 'correct': 'option3'},
        {'question': 'Which gas do plants absorb during photosynthesis?', 'option1': 'Oxygen',
         'option2': 'Carbon Dioxide', 'option3': 'Nitrogen', 'option4': 'Hydrogen', 'correct': 'option2'},
        {'question': 'In what year did the Titanic sink?', 'option1': '1910', 'option2': '1925', 'option3': '1932',
         'option4': '1912', 'correct': 'option4'},
        {'question': 'Who is known as the "Father of Computers"?', 'option1': 'Bill Gates', 'option2': 'Steve Jobs',
         'option3': 'Charles Babbage', 'option4': 'Alan Turing', 'correct': 'option3'},
        {'question': 'What is the currency of Brazil?', 'option1': 'Peso', 'option2': 'Yen', 'option3': 'Real',
         'option4': 'Euro', 'correct': 'option3'},
        {'question': 'Which famous scientist formulated the laws of motion and universal gravitation?',
         'option1': 'Nikola Tesla', 'option2': 'Isaac Newton', 'option3': 'Galileo Galilei',
         'option4': 'Stephen Hawking', 'correct': 'option2'},
        {'question': 'What is the main ingredient in guacamole?', 'option1': 'Tomato', 'option2': 'Onion',
         'option3': 'Avocado', 'option4': 'Lime', 'correct': 'option3'},
        {'question': 'Which country is known as the Land of the Rising Sun?', 'option1': 'China',
         'option2': 'South Korea', 'option3': 'Japan', 'option4': 'Vietnam', 'correct': 'option3'},
        {'question': 'Who wrote "To Kill a Mockingbird"?', 'option1': 'J.K. Rowling', 'option2': 'George Orwell',
         'option3': 'Harper Lee', 'option4': 'F. Scott Fitzgerald', 'correct': 'option3'},
    ]

    question_number = 0

    def update_room_user_list():
        socketio.emit('user_list', list(users.keys()), room=game_info['game_id'], namespace=namespace)

    @socketio.on('connect', namespace=namespace)
    def connect():
        print('Client joined the game')
        socketio.emit('hi', namespace=namespace)
        join_room(game_info['game_id'])
        print(f"Users in room {game_info['game_id']}, {users.keys()}")
        socketio.emit('user_list', list(users.keys()), room=request.sid, namespace=namespace)

    @socketio.on('disconnect', namespace=namespace)
    def disconnect():
        # Remove the user from users
        print(f"Users in room {game_info['game_id']}, {users.keys()}")
        if session.get('username') in users:
            users.pop(session.get('username'))
            update_room_user_list()
        if session.get('username') in answers:
            answers.pop(session.get('username'))

    @socketio.on('register', namespace=namespace)
    def register_user(username):
        session['username'] = username
        users[username] = request.sid
        points[username] = 0
        if len(points) == len(users):
            socketio.start_background_task(run_main_game)

    def run_main_game():
        nonlocal question_number, points, trivia_questions, answers
        while question_number < game_info['num_questions']:
            question = trivia_questions[question_number]
            socketio.emit('question', question, room=game_info['game_id'], namespace=namespace)
            answers.clear()

            correct_option = question['correct']

            @socketio.on('next_question', namespace=namespace)
            def next_question():
                nonlocal question_number
                question_number += 1
                if question_number <= game_info['num_questions']:
                    question = trivia_questions[question_number]
                    socketio.emit('question', question, room=game_info['game_id'], namespace=namespace)

                else:
                     # Emit the final points and game end event
                    socketio.emit('final_points', points, room=game_info['game_id'], namespace=namespace)
                    socketio.emit('game_end', room=game_info['game_id'], namespace=namespace)

            @socketio.on('answer', namespace=namespace)
            def receive_answer(data):
                if session.get('username') in users:
                    selected_option = data.get('option', None)

                    if selected_option == correct_option:
                        points[session.get('username')] = points.get(session.get('username'), 0) + 10
                        socketio.emit('correct', points, room=users[session.get('username')], namespace=namespace)
                    else:
                        socketio.emit('incorrect', points, room=users[session.get('username')], namespace=namespace)

            while len(answers) < len(users):
                socketio.sleep(1)

            question_number += 1

            # Emit updated points after each question
            socketio.emit('updated_points', points, room=game_info['game_id'], namespace=namespace)

            # Check if it's the last question
            if question_number == game_info['num_questions']:
                break

            socketio.sleep(2)

    
