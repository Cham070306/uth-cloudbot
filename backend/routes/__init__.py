from flask import Blueprint

api = Blueprint("api", __name__)

from routes import auth, chat, documents, feedback, health, personal  # noqa: E402,F401
