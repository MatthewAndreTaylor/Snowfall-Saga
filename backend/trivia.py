from flask import Flask, jsonify, request

app = Flask(__name__)

# example questions
trivia_questions = [
    {"id": 1, "question": "What is the capital of India?", "answer": "New Delhi"},
    {"id": 2, "question": "What is Melodi?", "answer": "Modi + Meloni"},
    {"id": 3, "question": "What is one word to describe Elvish Yadav?", "answer": "Sysstumm"},
    # Add more questions as needed
]

@app.route('/api/questions', methods=['GET'])
def get_questions():
    return jsonify(trivia_questions)

if __name__ == '__main__':
    app.run(debug=True)
