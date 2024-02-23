from flask import Blueprint, request
from .. import db
from ..models import User

leaderboard_handler = Blueprint(
    "leaderboard_handler",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@leaderboard_handler.route("/leaderboard", methods=["GET"])
def make_leaderboard():
    # get all the userrs from the database which is inside User table
    # Sort by the points and display the users: username -> points in dict.
    users = User.query.order_by(User.points.desc()).all()
    leaderboard = {
        user.username: user.points for user in users
    }  # Exxample: {"matt": 100, "john": 50}4

    prepaered_leaderboard = ["Rank | Username | Points"]
    for i, (username, points) in enumerate(leaderboard.items(), 1):
        prepaered_leaderboard.append(f"{i} | {username} | {points}")
    return "<br>".join(prepaered_leaderboard)
