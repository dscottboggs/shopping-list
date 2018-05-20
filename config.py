from misc_functions import get_entropy
from os.path import abspath, dirname, join
from os import environ

class Config:
    """Static configuration object."""
    debug = DEBUG_FLAG = True
    SECRET_KEY = get_entropy(500)
    SQLALCHEMY_DATABASE_URI = environ.get("SHOPPING_LIST_DB_URL")\
        or f"sqlite:///{join(abspath(dirname(__file__)))}/dev.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENTROPY_BITS = 500
    PUBLISH_PORT = 5000
    PROTO = "http"
    SERVER_URL = f"localhost:{PUBLISH_PORT}"
