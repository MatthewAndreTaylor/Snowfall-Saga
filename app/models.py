from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Class representing a user in the system.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user, should be unique.
        password (str): The hashed password of the user.

    Methods:
        to_dict(): Returns the user object as a dictionary.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def to_dict(self):
        """Converts the user object to a dictionary.

        Returns:
            dict: A dictionary containing user information.
        """
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
