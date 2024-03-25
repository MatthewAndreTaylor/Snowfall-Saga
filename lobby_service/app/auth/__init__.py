from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user
from .. import db, login_manager
from ..models import User

from better_profanity import profanity

profanity.load_censor_words_from_file("lobby_service/app/static/bad-words.txt")

login_view = Blueprint(
    "login_view",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets/auth",
)


@login_manager.user_loader
def load_user(user_id: int):
    return User.query.filter_by(id=int(user_id)).first()


@login_view.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    username = request.form.get("username")
    password = request.form.get("password")
    if username is None or password is None:
        return redirect("/login")

    user = User.query.filter_by(username=username).first()
    # Hash the users password
    password = User.hash_password(password)
    if user and user.verify_password(password):
        login_user(user)
        return redirect("/")
    flash("Invalid username or password")
    return redirect("/login")


@login_view.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")

    if username is None or password is None:
        return redirect(url_for("login_view.login"))

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("Username already exists. Please choose another username")
        return redirect("/login")

    if profanity.contains_profanity(username):
        flash("Username already exists. Please choose another username")
        return redirect("/login")

    # Hashing the user's password before adding it to the database
    password = User.hash_password(password)
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for("login_view.login"))
