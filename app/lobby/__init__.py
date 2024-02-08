from flask import Blueprint, render_template
from flask_login import login_required

lobby_view = Blueprint(
    "lobby_view",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets/lobby",
)


@lobby_view.route("/")
@login_required
def lobby():
    return render_template("lobby/index.html")
