from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import hashlib
import hmac

db = SQLAlchemy()
secret_salt = "mattsSecretSauce"


class User(UserMixin, db.Model):
    """Class representing a user in the system.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user, should be unique.
        password (str): The hashed password of the user.

    Methods:
        hash_password(): Returns a password hashed using SHA512
        verify_password(): Compares a password against a Users password
        to_dict(): Returns the user object as a dictionary.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

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
