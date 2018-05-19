"""Tests for the routes.py file in the interface_api module."""
from interface_api.routes import user_is_unauthorized
from interface_api.models import User
from config import Config
from misc_functions import build_url
from interface_api import db
from requests import get, post, delete, request, HTTPError
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

    def test_unauthorized_user(self):
        """Test that an unauthorized user receives a 401 error.

        Important NOTE: this should also verify that a request submitted with
        an invalid UID, or token is indistinguishable.
        """
        def check_method(method: str):
            """Check an unauthorized user for a particular method."""
            invalid_token_response = request(
                method=method
                url=self.api_endpoint,
                headers={
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

        for meth in self.valid_methods:
            check_method(meth)


class RequiresTestEntry(RequiresTestUser):
    """A superclass for tests that require a ListEntry object to work with.

    Subclassing this adds the "entry" object to your class, and a corresponding
    entry in the database.
    """
    valid_methods: Tuple[str...] = (,)

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
    valid_methods: Tuple[str...] = (,)

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
    api_endpoint = build_url(
        self.config.PROTO, self.config.SERVER_URL, "entry")
    entry_content = b"Simulated real content!"
    valid_methods: Tuple[str...] = ("GET", "POST", "DELETE")

    def test_valid_GET(self):
        """Test for a valid GET request for a valid DB row."""
        response = get(
            self.api_endpoint,
            headers={
                'uid':          self.user.identifier,
                'token':        self.token,
                'elementid':    self.entry.identifier,
            }
        )
        assert response.ok
        assert response.json['identifier'] == self.entry.identifier
        assert response.json['content'] == self.entry_content
        assert response.json['author'] == self.user.identifier
        assert response.json['creation_time'] == self.entry.creation_time
        # TODO: test for creation time to be actually near "now"
        response = get(
            self.api_endpoint,
            headers={
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
            self.api_endpoint,
            headers={
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

    def test_valid_POST(self):
        """Test POSTing an entry works."""
        response = post(
            self.api_endpoint,
            headers={
                'uid': self.user.identifier,
                'token': self.token
            },
            data=self.entry_content
        )
        assert response.ok
        assert response.status_code == 200
        assert response.json['content'] == self.entry_content
        assert response.json['author'] == self.user.identifier
        # TODO: test for creation time
        response = post(
            self.api_endpoint,
            headers={
                'uid': self.user.identifier,
                'token': self.token,
                'json': 0
            }
            data=self.entry_content
        )
        assert response.ok
        assert response.status_code == 200
        assert response.text == self.entry_content

    def test_invalid_POST(self):
        """Test various malformed POST requests for this endpoint"""
        too_long_content = dedent("""
            Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
            eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
            ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
            aliquip ex ea commodo consequat. Duis aute irure dolor in
            reprehenderit in voluptate velit esse cillum dolore eu fugiat
            nulla pariatur. Excepteur sint occaecat cupidatat non proident,
            sunt in culpa qui officia deserunt mollit anim id est laborum.""")

        @strict
        def too_long_content(json: bool):
            """Test for the response with json enabled or not."""
            response = post(
                self.api_endpoint,
                headers={
                    'uid': self.user.identifier,
                    'token': self.token,
                    'json': '1' if json else '0'
                }
                data={
                    self.entry_content
                }
            )
            assert not response.ok
            assert response.status_code == 400
            assert response.text == dedent(f"""
                Content is too long! Received {len(too_long_content)} chars,
                max 256.""")
        too_long_content(True)
        too_long_content(False)

    def test_valid_DELETE(self):
        """Test that a valid DELETE request deletes the associated row."""
        # beforehand, lets make sure the entry exists.
        assert ListEntry.query.get(self.entry.identifier).identifier \
            == self.entry.identifier
        assert ListEntry.query.get(self.entry.identifier).content\
            == self.entry_content
        assert str(ListEntry.query.get(self.entry.identifier)) \
            == self.entry_content
        assert ListEntry.query.get(self.entry.identifier).author \
            == self.user.identifier

        # A-Okay, let's delete it.
        response = delete(
            self.api_endpoint,
            headers={
                'uid': self.user.identifier,
                'token': self.token,
                'elementid': self.entry.identifier
            }
        )
        assert response.ok
        assert response.status_code == 200

        # and it's gone?
        with raises(SQLAlchemyError):
            ListEntry.query.get(self.entry.identifier)
        response = get(
            self.api_endpoint,
            headers={
                'uid': self.user.identifier,
                'token': self.token,
                'elementid': self.entry.identifier
            }
        )
        assert not response.ok
        assert response.status_code == 400
        assert response.text == "Invalid entry ID."

    def test_invalid_DELETE(self):
        """Test for the proper results from an invalid DELETE request."""
        response = delete(
            self.api_endpoint,
            headers={
                'uid': self.user.identifier,
                'token': self.token,
                'elementid': -1
            }
        )
        assert not response.ok
        assert response.status_code == 400
        assert response.text == f"Couldn't delete row -1."


class TestListEntries(RequiresTestUser):
    """Tests for the list_entries endpoint."""

    api_endpoint = build_url(self.config.PROTO, self.config.SERVER_URL, "list")
    valid_methods: Tuple[str...] = ("GET")

    @property
    @strict
    def entries(self) -> List[Dict[str, Union[int, str]]]:
        """A list of the attributes of each entry in the database."""
        try:
            return self._entries
        except AttributeError:
            self._entries = [
                loads(entry.json) for entry in ListEntry.query.all()
            ]
            return self._entries

    def test_valid_query(self):
        """Check that an authorized query returns the correct values."""
        response = get(
            self.api_endpoint,
            headers={
                'uid': self.user.identifier,
                'token': self.token
            }
        )
        assert response.ok
        assert response.status_code == 200
        assert response.json == self.entries

    def test_invalid_query(self):
        """Test for a malformed request.

        TODO as there really isn't a way to make an authenticated, malformed
        request, and authentication is already being tested by the
        RequiresTestUser superclass.
        """
        pass
