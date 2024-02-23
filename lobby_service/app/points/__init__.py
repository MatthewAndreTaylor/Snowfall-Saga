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


def update_database(username, points):
    user = User.query.filter_by(username=username).first()
    user.points += points
    print(user.points)
    db.session.commit()
