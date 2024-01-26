from flask import Blueprint

lobby = Blueprint(
    "lobby",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="assets",
)


@lobby.route("/")
def home():
    return "Hello World"
