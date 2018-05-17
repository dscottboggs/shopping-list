"""Tests for the routes.py file in the interface_api module."""
from interface_api.routes import user_is_unauthorized
from interface_api.models import User
from config import Config
from misc_functions import build_url
from interface_api import db
from requests import get, HTTPError
from strict_hint import strict


class RequiresTestUser:
    """A mixin for tests that require a User object.

    A class MUST have a "user_name" attribute in order to subclass this. The
    user_name attribute SHOULD be a string, but technically can be anything
    with a reasonable __str__() representation.

    Defining the user, committing it to the database, and retrieving its plain-
    text token require that the SQLAlchemy attribute be imported as db from the
    package.

    Subclassing this allows the subclassed object access to the 'user' and
    'token' attributes, which represent an interface_api.models.User and a
    bytestring representing the alphanumeric representation of said user's
    raw token.
    """

    invalid_token = b"invalid token"

    def setup_method(self):
        """Create a User to check for, commit it, and store its token."""
        self.user = User(str(self.user_name))

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

class RequiresTestEntry(RequiresTestUser):
    """A superclass for tests that require a ListEntry object to work with.

    Subclassing this adds the "entry" object to your class, and a corresponding
    entry in the database.
    """

    def setup_method(self):
        """Create a ListEntry object to work with and commit it.

        Calls the superclass's setup method before running.
        """
        super().setup_method()  # we need a 'user'.
        self.entry = ListEntry(str(self.entry_content, self.user.identifier))
        db.session.add(self.entry)
        db.session.commit()

    def teardown_method(self):
        """Delete the created ListEntry row from the database.

        Calls the superclass's teardown method after running.
        """
        ListEntry.query.get(self.entry.identifier).delete()
        db.session.commit()
        super().teardown_method()

class TestUserIsUnauthorized(RequiresTestUser):
    """Tests for the "user_is_unauthorized" function."""
    user_name = "TestUserIsUnauthorized User"
    token: bytes

    def test_invalid_token(self):
        """Check for a True response after giving an invalid token."""
        assert user_is_unauthorized(self.user.identifier, self.invalid_token)

    def test_valid_token(self):
        """Check for a False response after giving the valid token."""
        assert not user_is_unauthorized(self.user.identifier, self.token)

    def test_invalid_user_ID(self):
        """Check that an invalid User ID is handled properly."""
        assert user_is_unauthorized(-1, self.token)


class TestEntry(RequiresTestEntry):
    """Tests for the "/entry" entrypoint."""

    user_name = "TestEntry User"
    token: bytes
    api_endpoint = f"{Config.server_url}/entry"
    entry_content = "Simulated real content!"

    def test_unauthorized_user(self):
        """Test that an unauthorized user receives a 401 error.

        Important NOTE: this should also verify that a request submitted with
        an invalid UID, or token is indistinguishable.
        """
        invalid_token_response = get(
            build_url(self.config.PROTO, self.config.SERVER_URL, "entry"),
            data={
                "uid":          self.user.identifier,
                "token":        self.invalid_token,
                "elementid":    self.entry.identifier,
            }
        )
        assert not invalid_token_response.ok
        assert invalid_token_response.status_code = 401
        assert invalid_token_response.text == "Unauthorized"
        with raises(HTTPError):
            invalid_token_response.raise_for_status()

        invalid_user_response = get(
            build_url(self.config.PROTO, self.config.SERVER_URL, "entry"),
            data={
                'uid':          -1,
                'token':        b'Correct type, invalid token.',
                'elementid':    self.entry.identifier
            }
        )
        assert not invalid_user_response.ok
        assert invalid_user_response.status_code == 401
        assert invalid_token_response.text == "Unauthorized"
        with raises(HTTPError):
            invalid_user_response.raise_for_status()

        for attr in invalid_token_response:
            assert invalid_user_response.__dict__[attr]\
                == invalid_token_response.__dict__[attr],\
                "Attribute %s doesn't match" % attr

    def test_valid_GET(self):
        """Test for a valid GET request for a valid DB row."""
        response = get(
            build_url(self.config.PROTO, self.config.SERVER_URL, "entry"),
            data={
                'uid':          self.user.identifier,
                'token':        self.token,
                'elementid':    self.entry.identifier,
            }
        )
        assert response.ok
        assert response.json['identifier'] = self.entry.identifier
        assert response.json['content'] = self.entry_content
        assert response.json['author'] = self.user.identifier
        # TODO: test for creation time
        response = get(
            build_url(self.config.PROTO, self.config.SERVER_URL, "entry"),
            data={
                'uid':          self.user.identifier,
                'token':        self.token,
                'elementid':    self.entry.identifier,
                'json':         0,
            }
        )
        assert response.ok
        assert response.text == self.test_content

    def test_invalid_GET(arg):
        """Test that an invalid GET request is handled properly."""
        response = get(
            build_url(self.config.PROTO, self.config.SERVER_URL, "entry"),
            data={
                'uid':          self.user.identifier,
                'token':        self.token,
                'elementid':    -1,
            }
        )
        assert not response.ok
        assert response.status_code == 400
        assert response.text == "Invalid entry ID."
        with raises(HTTPError):
            response.raise_for_status()
