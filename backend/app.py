from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from config import Config, get_port
from routes import api


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    app.register_blueprint(api, url_prefix="/api")

    def error_response(code, message, status):
        return jsonify({"error": {"code": code, "message": message}}), status

    @app.errorhandler(400)
    def bad_request(_error):
        return error_response("INVALID_REQUEST", "Yêu cầu không hợp lệ.", 400)

    @app.errorhandler(404)
    def not_found(_error):
        return error_response("NOT_FOUND", "Endpoint không tồn tại.", 404)

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return error_response("METHOD_NOT_ALLOWED", "Phương thức HTTP không được hỗ trợ.", 405)

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(_error):
        return error_response("REQUEST_TOO_LARGE", "Kích thước request vượt quá giới hạn.", 413)

    @app.errorhandler(Exception)
    def internal_error(error):
        if isinstance(error, HTTPException):
            return error
        app.logger.exception("Unexpected server error")
        return error_response("INTERNAL_ERROR", "Máy chủ gặp lỗi không mong đợi.", 500)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=get_port(), debug=False)
