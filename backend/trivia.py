# app.py (Flask backend)

from flask import Flask, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Sample questions and answers (replace with your actual data or connect to a database)
questions = [
    {"id": 1, "question": "What is the capital of France?", "options": ["Paris", "Berlin", "Madrid", "Rome"], "answer": "Paris"},
    {"id": 2, "question": "What is 2 + 2?", "options": ["4", "6", "8", "10"], "answer": 4},
    # Add more questions as needed
]

@app.route('/questions', methods=['GET'])
def get_questions():
    # Return a list of questions without answers for the TriviaGamepad.js questions list
    questions_list = [{"id": q["id"], "question": q["question"]} for q in questions]
    return jsonify(questions_list)

@app.route('/questions/<int:question_id>/options', methods=['GET'])
def get_answers(question_id):
    # Return the answers for a specific question
    question = next((q for q in questions if q["id"] == question_id), None)
    if question:
        return jsonify({"choices": question["options"], "answer": question["answer"]})
    else:
        return jsonify({"error": "Question not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
