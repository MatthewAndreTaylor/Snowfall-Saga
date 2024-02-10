from flask import Flask
from flask_login import LoginManager
from models import db, User

app = Flask(__name__)
app.secret_key = "MYSECRET"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///accounts.db"

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login_view.login"
login_manager.init_app(app)

secret_salt = "mattsSecretSauce"


@login_manager.user_loader
def load_user(user_id: int):
    return User.query.filter_by(id=int(user_id)).first()


from auth import login_view

app.register_blueprint(login_view)

from lobby import lobby_view

app.register_blueprint(lobby_view)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
