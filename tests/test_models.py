from api import db
from api.models import User, ListEntry
from datetime import datetime
from strict_hint import strict
from typing import Union


def add_to_db(model_instance):
    """Add the given element to the app's database."""
    db.session.add(model_instance)
    db.session.commit


class TestUser:
    """Tests for the User model."""
    name = "Test User"
    def setup_method(self):
        """Get a User object to work with."""
        self.user = User(self.name)
        add_to_db(self.user)

    def teardown_method(self):
        """Remove the earlier created User."""
        User.query.get(self.user.identifier).delete()

    def test_attributes(self):
        """Test the attributes of the User object."""
        assert User.query.get(self.user.identifier).identifier \
            == self.user.identifier
        assert User.query.get(self.user.identifier).readable_name == self.name
        assert self.user.get_id() == self.user.identifier

    def test_token(self):
        """Test the new_token and check_token attributes."""
        def cb(tk: bytes):
            assert User.query.get(self.user.identifier).check_token(tk)
        self.user.new_token(cb)


class TestListEntry:
    """Tests for the ListEntry model."""

    name = "Test User"
    content = "Test content value."

    def setup_method(self):
        self.setup_time = datetime.now()
        self.user = User(self.name)
        add_to_db(self.user)
        self.entry = ListEntry(self.content, self.user.identifier)
        add_to_db(self.entry)

    def teardown_method(self):
        """Delete the earlier created database entries."""
        self.entry.delete()
        self.user.delete()

    def test_creation_time(self):
        """Test that the creation time is close to now.

        Might need revised to allow more time.
        """
        assert int(self.setup_time.timestamp()) \
            == int(ListEntry.query.get(self.entry.identifier).creation_time)

    def test_content(self):
        """Test content value."""
        assert self.content \
            == ListEntry.query.get(self.entry.identifier).content

    def test_author(self):
        """Test the author relation."""
        assert self.name == User.query.get(
            ListEntry.query.get(self.entry.identifier).author
        )
