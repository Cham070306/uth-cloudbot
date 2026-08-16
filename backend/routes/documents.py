from flask import jsonify, request

from repositories import get_repository
from routes import api


@api.get("/documents")
def documents():
    category = request.args.get("category", "").strip()
    filters = {"category": category} if category else {}
    return jsonify({"items": get_repository().list("documents", **filters)})
