from flask import Blueprint

api = Blueprint("api", __name__)

from routes import chat, feedback, health  # noqa: E402,F401
