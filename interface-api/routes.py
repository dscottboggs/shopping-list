from flask import request as incoming_request
from config import Config


@app.route("/entry", methods=["GET", "POST", "DELETE"])
def entry():

if __name__ == '__main__':
    app.run(port=Config.PUBLISH_PORT)
