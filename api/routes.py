from flask import request as incoming_request, make_response
from json import dumps as toJSONtext, loads as fromJSONtext
from strict_hint import strict
from sqlalchemy.exc import SQLAlchemyError
from api import app
from api.models import ListEntry
from config import Config


@strict
def user_is_unauthorized(id: int, token: bytes) -> bool:
    """Check if the given user is authorized, and return False if so."""
    from api.models import User
    try:
        user = User.query.get(id)
    except SQLAlchemyError:
        return True
    if user:
        return not user.check_token(token)
    return True


@app.route("/entry", methods=["GET", "POST", "DELETE"])
def entry():
    """Retrieve, create, or delete a list entry for an authenticated user.

    Accepted headers for this endpoint:
    uid:        The user's ID number (their primary key)
    token:      The user's authentication token
    elementid:  The ID (primary key) of the element to be acted upon.
    json:       If "0", only the content of the specified entry is returned.
                For any other value, the JSON encoded attributes of the entry
                is returned. (only applies to GET requests)
    encoding:   The text encoding of the content of the POST request. Defaults
                to UTF-8.

    A POST request can accept a string of up to 256 characters long to be saved
    as the content of the Entry.

    Actions taken per method:
    Method  Code    Explanation             Body
    GET:    200  -  Valid request           Either the content of the entry as
                                            a string (if the 'json' request
                                            value is '0') or its JSON-encoded
                                            attributes.
            400  -  Malformed request       Descriptive error.
            401  -  User authentication     Lit. "Unauthorized."
                    failed.
    POST:   Creates a new entry with the provided content, authored by the
            authenticated user.
        Responses:
            Same as for get requests, including returning the JSON-encoded (or
            plain-text) content of the submitted entry.
    DELETE: Deletes the specified row in the database
        Responses:
            200  -  Valid request           Lit. "success"
            400  -  Same as for GET/POST requests.
            401  -  Same as for GET/POST requests.
    """
    if user_is_unauthorized(             # WARNING: this block must come first!
                int(incoming_request.headers.get("uid")),
                incoming_request.headers.get('token')
            ):
        return ("Unauthorized", 401)
    from api import db
    from api.models import ListEntry
    if incoming_request.method == "GET":
        try:
            if incoming_request.headers.get("json") == "0":
                response = str(
                    ListEntry.query.get(
                        incoming_request.headers.get("elementid")
                    )
                )
                response.headers['Content-Type'] = 'text/plain'
            else:
                response = ListEntry.query.get(
                    incoming_request.headers.get("elementid")
                ).json
                response.headers['Content-Type'] = 'application/json'
        except SQLAlchemyError:
            response = make_response("Invalid entry ID.", 400)
        return response
    if incoming_request.method == "POST":
        content: str = incoming_request.data.decode(
            incoming_request.headers.get('encoding') or 'utf-8'
        )
        if len(content) > 256:
            return (
                "Content is too long! Received %s chars, max 256."
                    % len(content),
                400
            )
        the_entry = ListEntry(
            content=content,
            author=incoming_request.headers.get("uid")
        )
        db.session.add(the_entry)
        db.session.commit
        return (the_entry.json, 200)
    if incoming_request.method == "DELETE":
        try:
            ListEntry.query.get(
                incoming_request.headers.get("elementid")
            ).delete()
            return ("success", 200)
        except SQLAlchemyError:
            return (
                "Couldn't delete row %s."
                    % incoming_request.headers.get('elementid'),
                400
            )


@app.route("/list")
def list_entries():
    """JSON-encoded list of all database entries and the content."""
    if user_is_unauthorized(
                incoming_request.headers.get("uid"),
                incoming_request.headers.get('token')
            ):
        return ("Unauthorized", 401)
    response = make_response(
        toJSONtext([
            fromJSONtext(entry.json) for entry in ListEntry.query.all()
        ]),
        200
    )
    response.headers['Content-Type'] = 'application/json'
    return response


if __name__ == '__main__':
    app.run(port=Config.PUBLISH_PORT)
