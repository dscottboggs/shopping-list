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
