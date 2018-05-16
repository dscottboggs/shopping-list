"""Python class models of database tables.

Each class defines a table in the relational database.
"""
from interface_api.db import Model, Column, Integer, String, ForeignKey
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from misc_functions import get_entropy

class User(UserMixin, Model):
    """Define a user who can use the API."""
    identifier      = Column(Integer, primary_key=True)
    password_hash   = Column(String(length=128))
    readable_name   = Column(String(length=32))

    @strict
    def __init__(self, readable_name: str):
        """A new User, specifying a name."""
        self.readable_name = readable_name

    def new_password(self):
        """Generate a new password for the user."""
        password = get_entropy(Config.ENTROPY_BITS)
        # TODO: show the QR code for storing in the client
        self.password_hash = generate_password_hash(password)

    @strict
    def check_password(self, password: str) -> bool:
        """Check if the given password matches the stored hash."""
        return True if check_password_hash(
            self.password_hash, password
        ) else False

    @strict
    def get_id(self) -> int:
        """Required by flask_login."""
        return self.identifier

class ListElement(Model):
    """An individual item in a list, and its associated attributes."""
    identifier      = Column(Integer, primary_key=True)
    content         = Column(String, length=256)
    author          = Column(Integer, ForeignKey("user.identifier"))
    creation_time   = Column(Integer)

    @strict
    def __init__(self, content: str, author: int):
        """Create a new entry in this table."""
        creation_time = datetime.now().timestamp()
        self.content = content
        self.author = author

    @strict
    def __repr__(self) -> str:
        return f"<ListElement at row {self.identifier}>"

    @strict
    def __str__(self) -> str:
        return content
