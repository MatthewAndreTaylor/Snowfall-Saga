from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user
from models import db, User
import hashlib
import hmac

login_view = Blueprint(
    "login_view",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets/auth",
)

secret_salt = "mattsSecretSauce"


@login_view.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    username = request.form.get("username")
    password = request.form.get("password")
    user = User.query.filter_by(username=username).first()

    # Hash the users password
    password = hmac.new(
        secret_salt.encode(), password.encode(), hashlib.sha512
    ).hexdigest()

    if user and hmac.compare_digest(user.password, password):
        login_user(user)
        return redirect(url_for("lobby_view.lobby"))
    return redirect(url_for("login_view.login"))


@login_view.route("/register", methods=["GET", "POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return "Username already exists. Please choose a different username."

    # Hashing the user's password before adding it to the database
    password = hmac.new(
        secret_salt.encode(), password.encode(), hashlib.sha512
    ).hexdigest()
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for("login_view.login"))
