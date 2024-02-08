from flask import Flask
from lobby import lobby_view

app = Flask(__name__)

app.register_blueprint(lobby_view)

if __name__ == "__main__":
    app.run(debug=True)
