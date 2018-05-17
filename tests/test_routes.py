"""Tests for the routes.py file in the interface_api module."""
from interface_api.routes import user_is_unauthorized
from interface_api.models import User
from interface_api import db
from requests import get
from strict_hint import strict


class TestUserIsUnauthorized:
    """Tests for the "user_is_unauthorized" function."""
    user_name = "Test User"
    invalid_token = b"invalid token"
    token: bytes

    def setup_method(self):
        """Create a User to check for and store its token."""
        self.user = User(self.user_name)

        @strict
        def cb(user_token: bytes, user, db, testobj):
            """The callback funtion to be used by new_token.

            Handles committing the User to the database."""
            testobj.token = user_token
            db.session.add(user)
            db.session.commit()
        self.user.new_token(cb, user=self.user, db=db, testobj=self)

    def teardown_method(self):
        """Delete the User we created."""
        User.query.get(self.user.identifier).delete()
        db.session.commit()

    def test_invalid_token(self):
        """Check for a True response after giving an invalid token."""
        assert user_is_unauthorized(self.user.identifier, self.invalid_token)

    def test_valid_token(self):
        """Check for a False response after giving the valid token."""
        assert not user_is_unauthorized(self.user.identifier, self.token)
