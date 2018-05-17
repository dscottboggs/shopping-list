from flask import request as incoming_request
from inteface_api import app
from config import Config
from strict_hint import strict
from sqlalchemy.exc import SQLAlchemyError


@strict
def user_is_unauthorized(id: int, token: bytes) -> bool:
    """Check if the given user is authorized, and return False if so."""
    from interface_api.models import User
    try:
        user = User.query.get(id)
    except SQLAlchemyError:
        return True
    if user:
        return not user.check_token(token)
    return True


@app.route("/entry", methods=["GET", "POST", "DELETE"])
def entry():
    """Retrieve, create, or delete a list entry.

    Accepted arguments for this endpoint:
    uid:        The user's ID number (their primary key)
    token:      The user's authentication token
    elementid:  The ID (primary key) of the element to be acted upon.
    json:       If "0", only the content of the specified entry is returned.
                For any other value, the JSON encoded attributes of the entry
                is returned. (only applies to GET requests)
    content:    A string of up to 256 characters long to be saved as the
                content of the Entry. (only applies to POST requests)
    """
    try:
        assert isinstance(uid, int), uid
        assert isinstance(token, bytes), token
        assert isinstance(elementid, int), elementid
        assert isinstance(json, int), json
        assert isinstance(content, str), content
    except AssertionError as e:
        return (f"{e.args[0]} is an invalid type.", 400)
    if len(content) > 256:
        return (
            f"Content is too long! Received {len(content)} chars, max 256.",
            400
        )
    if user_is_unauthorized(
                int(incoming_request.values.get("uid")),
                incoming_request.values.get('token')
            ):
        return ("Unauthorized", 401)
    from interface_api import db
    from interface_api.models import ListEntry
    if incoming_request.method == "GET":
        try:
            return str(
                ListEntry.query.get(incoming_request.values.get("elementid"))
            ) if incoming_request.values.get("json") == "0"\
                else ListEntry.query.get(
                    incoming_request.values.get("elementid")
                ).json
        except SQLAlchemyError:
            return ("Invalid entry ID.", 400)
    if incoming_request.method == "POST":
        the_entry = ListEntry(
            content=incoming_request.values.get("content"),
            author=incoming_request.values.get("uid")
        )
        db.session.add(the_entry)
        db.session.commit
        return (the_entry.json, 200)
    if incoming_request.method == "DELETE":
        try:
            ListEntry.query.get(
                incoming_request.values.get("elementid")
            ).delete()
            return ("success", 200)
        except SQLAlchemyError:
            return (
                "Couldn't delete row %s"
                    % incoming_request.values.get('elementid'),
                400
            )

@app.route("/list")
def list_entries():
    if user_is_unauthorized(
                incoming_request.values.get("uid"),
                incoming_request.values.get('token')
            ):
        return ("Unauthorized", 401)
    return (dumps([loads(entry.json) for entry in ListEntry.query.all()]), 200)

@app.route("/")
def display_list():
    if user_is_unauthorized(
                incoming_request.values.get("uid"),
                incoming_request.values.get('token')
            ):
        return ("Unauthorized", 401)
    return render_template(
        "display_list.html",
        title="List",
        listvals=[loads(entry.json) for entry in ListEntry.query.all]
    )

if __name__ == '__main__':
    app.run(port=Config.PUBLISH_PORT)
