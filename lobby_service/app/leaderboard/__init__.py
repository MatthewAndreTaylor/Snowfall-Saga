from flask import Blueprint, render_template
from flask_login import current_user
from ..models import User

leaderboard_handler = Blueprint(
    "leaderboard_handler",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets/leaderboard",
)


@leaderboard_handler.route("/leaderboard", methods=["GET"])
def make_leaderboard():
    # Get all the users from the database which is inside User table
    # Sort by the points and display the users: rank, username, points
    users = User.query.order_by(User.points.desc()).all()
    ranked_users = [(i + 1, user.username, user.points) for i, user in enumerate(users)]

    return render_template(
        "leaderboard/index.html",
        ranked_users=ranked_users,
        current_user_name=current_user.username,
    )
