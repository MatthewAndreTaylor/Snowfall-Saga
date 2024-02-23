from flask import Blueprint, render_template
from flask_login import current_user, login_required
from simple_websocket import ConnectionClosed
from flask_sock import Sock
import json
from .. import db
from ..models import User

store_view = Blueprint(
    "store_view",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/assets/store",
)

sock = Sock(store_view)

# Mapping of connections to current user id's
clients = {}
users = {}

# Bit representation of available sprites - 0 means for sale, 1 means
# not for sale - add leading 1 to denote amount of costumes
on_sale = 71  # 1 000 111 (leading purchasable default)

# Renders the store page
@store_view.route("/store")
@login_required
def store():
    return render_template(
        "store/store.html", player_points=current_user.points, on_sale=load_sprite()
    )


@sock.route("/purchase")
@login_required
def purchase(connection):
    process_purchase(connection, curr_user=current_user)


def process_purchase(connection, curr_user):
    if connection in clients:
        return

    # In the case of a test, the current user does not exist
    if curr_user is None:
        curr_user = User()
        curr_user.username = "TestUser"
        curr_user.points = 250
        curr_user.sprite_inventory = 7

    clients[connection] = curr_user.username
    users[curr_user.username] = connection

    while True:
        try:
            event = connection.receive()
            data = json.loads(event)

            if data["type"] == "purchase":
                # Check funds
                if curr_user.points >= 100:
                    update_inventory(data["sprite"], curr_user)
                    message = {
                        "type": "purchaseSuccess",
                        "sprite": data["sprite"],
                        "points": curr_user.points,
                    }
                    connection.send(json.dumps(message))
                else:
                    message = {
                        "type": "purchaseFailure",
                        "sprite": data["sprite"],
                    }
                    connection.send(json.dumps(message))

        except (KeyError, ConnectionError, ConnectionClosed):
            user = clients[connection]
            del clients[connection]
            del users[user]
            print(f"Store Removed connection {connection}")
            break


# Uses bitwise operation OR to check which sprites a user both
# does not own and is on sale
def load_sprite():
    """Queries the user and obtains their inventory sprites to see
    which sprites they can purchase of those for sale.
    """
    user = User.query.filter_by(username=current_user.username).first()
    sprite_inventory = user.sprite_inventory

    for_purchase = sprite_inventory | on_sale  # use bitwise OR
    purchase_bin = bin(for_purchase)[2:][
        ::-1
    ]  # reverse so least significant bit is at index 0
    indices = [
        index for index, char in enumerate(purchase_bin) if char == "0"
    ]  # indices of 0s
    return indices


# Adds purchased sprite to player's inventory and commits to database
def update_inventory(sprite, curr_user):
    """Updates a user's sprite inventory after making a successful purchase.

    Args:
        sprite (int): The n-th bit that represents the costume.
    """
    # For testing purposes
    if not curr_user.id:
        curr_user.points -= 100
        curr_user.sprite_inventory = curr_user.sprite_inventory | 1 << sprite
        return

    user = User.query.filter_by(username=curr_user.username).first()
    user.points -= 100
    user.sprite_inventory = user.sprite_inventory | 1 << sprite
    db.session.commit()
