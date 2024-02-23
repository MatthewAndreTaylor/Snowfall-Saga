from flask_login import UserMixin
from . import db
import hashlib
import hmac


secret_salt = "mattsSecretSauce"


class User(UserMixin, db.Model):
    """Class representing a user in the system.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user, should be unique.
        password (str): The hashed password of the user.
        sprite (int): The sprite index of the current user.
        sprite_inventory (int): A bit representation of the owned sprites of the user.

    Methods:
        hash_password(): Returns a password hashed using SHA512
        verify_password(): Compares a password against a Users password
        to_dict(): Returns the user object as a dictionary.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    sprite = db.Column(
        db.Integer, default=0, nullable=False
    )  # Default sprite at index 0
    sprite_inventory = db.Column(
        db.Integer, default=7, nullable=False
    )  # Initial access to sprites at indexes 0 to 2

    @staticmethod
    def hash_password(password):
        return hmac.new(
            secret_salt.encode(), password.encode(), hashlib.sha512
        ).hexdigest()

    def verify_password(self, password):
        return hmac.compare_digest(self.password, password)

    def to_dict(self):
        """Converts the user object to a dictionary.

        Returns:
            dict: A dictionary containing user information.
        """
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


class Friendship(db.Model):
    """Class representing a friendship between two users.

    Attributes:
        user_id (int): The id of the user who sent the friend request.
        friend_id (int): The id of the user who received the friend request.
        status (int): The status of the friendship request. 0 for pending, 1 for accepted, 2 for declined.

    Methods:
        to_dict(): Returns the friendship object as a dictionary.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        """Converts the friendship object to a dictionary.

        Returns:
            dict: A dictionary containing friendship information.
        """
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
