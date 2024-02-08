from flask import Blueprint, render_template

lobby_view = Blueprint(
    "lobby_view",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets",
)


@lobby_view.route("/")
def home():
    return render_template("lobby/index.html")
