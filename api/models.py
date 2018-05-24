"""Python class models of database tables.

Each class defines a table in the relational database.
"""
from api import db      # Model, Column, Integer, String, ForeignKey
from config import Config
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from misc_functions import get_entropy
from json import dumps
from typing import Callable, Optional, Any
from strict_hint import strict


class User(UserMixin, db.Model):
    """Define a user who can use the API."""
    identifier      = db.Column(db.Integer, primary_key=True)
    token_hash      = db.Column(db.String(length=128))
    readable_name   = db.Column(db.String(length=32))

    @strict
    def __init__(self, readable_name: str):
        """A new User, specifying a name."""
        self.config = Config()
        self.readable_name = readable_name

    #@strict  # or not...
    def new_token(
                self,
                callback: Optional[Callable[[bytes], None]]=None,
                *cbargs,
                **cbkwargs
            ):
        """Generate a new token for the user.

        Callback is a function to accept and handle the raw token. It defaults
        to print, but should be set to something else. My plan is to make the
        server's default to display a QR code. Returns the result of callback.

        Any additional arguments can be specified to be passed to the callback
        function. Just don't forget when writing your callback that the token
        is the first argument. The token is an alphanumeric bytes string.

        For example, your callback function will need to handle committing the
        User to the given database. so a call to new_token might look like
            user.new_token(cbfunc, user, db)
        where user the object representing this class, and db is the database.
        """
        if callback is None:
            callback = print
        token = get_entropy(self.config.ENTROPY_BITS)
        self.token_hash = generate_password_hash(token)
        return callback(token, *cbargs, **cbkwargs)

    @strict
    def check_token(self, token: str) -> bool:
        """Check if the given token matches the stored hash."""
        return True if check_password_hash(
            self.token_hash, token
        ) else False

    @strict
    def get_id(self) -> int:
        """Required by flask_login."""
        return self.identifier


class ListEntry(db.Model):
    """An individual item in a list, and its associated attributes."""
    identifier      = db.Column(db.Integer, primary_key=True)
    content         = db.Column(db.String(length=256))
    author          = db.Column(db.Integer, db.ForeignKey("user.identifier"))
    creation_time   = db.Column(db.Integer)

    @strict
    def __init__(self, content: str, author: int):
        """Create a new entry in this table."""
        self.creation_time = datetime.now().timestamp()
        self.content = content
        self.author = author

    @strict
    def __repr__(self) -> str:
        """The object representation of the object."""
        return f"<ListEntry at row {self.identifier}>"

    @strict
    def __str__(self) -> str:
        """The string representation of the object."""
        return self.content

    @property
    @strict
    def json(self) -> str:
        """JSON encoding of attributes."""
        return dumps({
            'identifier':       self.identifier,
            'content':          self.content,
            'author':           self.author,
            'creation_time':    self.creation_time
        })
