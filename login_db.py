import sqlite3

class LoginDB:
    def __init__(self, db_path):
        self.connect = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connect.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users ( id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT NOT NULL,
                       password TEXT NOT NULL)''')
        self.connect.commit()
    
    def close(self):
        self.connect.close()
    
    def login(self, username, password):
        self.cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        return self.cursor.fetchone()
    
    def check_user_exist(self, username):
        self.cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        return self.cursor.fetchone()
    
    def register(self, username, password):
        self.cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        self.connect.commit()
        self.connect.close()