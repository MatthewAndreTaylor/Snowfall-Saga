from collections import deque


class User:
    def __init__(self, username):
        self.username = username
        self.typed = ""
        self.correct = 0
        self.incorrect = 0
        self.wpm = 0
        self.wpm_queue = deque(maxlen=20)
        self.text_pos = 0
        self.position = 0
        self.done = False
        self.standings = ""
