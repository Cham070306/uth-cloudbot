from flask import jsonify

from routes import api


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "uth-cloudbot-backend"})
