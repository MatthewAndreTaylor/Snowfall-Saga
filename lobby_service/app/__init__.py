from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.secret_key = "MYSECRET"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///accounts.db"

    db.init_app(app)

    login_manager.login_view = "login_view.login"
    login_manager.init_app(app)

    with app.app_context():
        from .auth import login_view

        app.register_blueprint(login_view)

        from .lobby import lobby_view

        app.register_blueprint(lobby_view)

        from .messages import messenger

        app.register_blueprint(messenger)

        from .points import points_handler

        app.register_blueprint(points_handler)

        from .leaderboard import leaderboard_handler

        app.register_blueprint(leaderboard_handler)

    with app.app_context():
        db.create_all()

    return app
