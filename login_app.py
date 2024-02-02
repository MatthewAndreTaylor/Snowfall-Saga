from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from login_db import LoginDB

app = Flask(__name__)

DATABASE = 'your_database.db'
db = LoginDB(DATABASE)

@app.route('/')
def index():
    return render_template('login2.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Check credentials against the database
    user = db.login(username, password)
    #db.close()

    if user:
        # Successful login
        return f'Welcome, {username}!'
    else:
        # Invalid credentials, redirect back to the login page
        return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    # Check if the username already exists in the database
    existing_user = db.check_user_exist(username)

    if existing_user:
        return 'Username already exists. Please choose another username.'
    else:
        # Insert the new user into the database
        db.register(username, password)
        return 'Account created successfully. You can now log in.'

if __name__ == '__main__':
    app.run(port=5001, debug=True)