from flask import Blueprint, request
from .. import db
from ..models import User

points_handler = Blueprint(
    "points_handler",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@points_handler.route("/points", methods=["POST"])
def update_points():
    data = request.json
    for key in data:
        update_database(key, data[key])
    return "Success!", 200


def update_database(username: str, points: int):
    """Update the points of a user in the database.

    Args:
        username (str): The username of the user.
        points (int): The number of points to add to the user's current points.
    """
    user = User.query.filter_by(username=username).first()
    user.points += points
    db.session.commit()
