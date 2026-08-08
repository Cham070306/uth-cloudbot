import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app({"TESTING": True})
    return app.test_client()


def assert_error(response, status):
    assert response.status_code == status
    assert response.is_json
    assert set(response.get_json()["error"]) == {"code", "message"}


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "uth-cloudbot-backend"}


def test_chat_valid(client):
    response = client.post("/api/chat", json={"message": "UTH CloudBot hỗ trợ gì?"})
    data = response.get_json()
    assert response.status_code == 200
    assert {"answer", "intent", "source", "latency_ms"} <= data.keys()
    assert data["intent"] == "unknown"
    assert data["source"]["type"] == "mock"
    assert isinstance(data["latency_ms"], int) and data["latency_ms"] >= 0


@pytest.mark.parametrize("payload", [{}, {"message": ""}, {"message": "   "}, {"message": 123}])
def test_chat_invalid_message(client, payload):
    assert_error(client.post("/api/chat", json=payload), 400)


def test_chat_too_long(client):
    assert_error(client.post("/api/chat", json={"message": "a" * 2001}), 400)


def test_chat_non_json(client):
    assert_error(client.post("/api/chat", data="message=test", content_type="text/plain"), 400)


def test_chat_fe01_compatibility(client):
    response = client.post("/api/chat", json={"question": "Câu hỏi từ FE-01"})
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data["paragraphs"], list)
    assert isinstance(data["sources"], list)


def test_feedback_valid(client):
    response = client.post("/api/feedback", json={"message_id": "demo-message-001", "helpful": True})
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "received", "message_id": "demo-message-001", "helpful": True
    }


@pytest.mark.parametrize(
    "payload",
    [{"helpful": True}, {"message_id": "", "helpful": True}, {"message_id": "id"},
     {"message_id": "id", "helpful": "true"}],
)
def test_feedback_invalid(client, payload):
    assert_error(client.post("/api/feedback", json=payload), 400)


def test_feedback_fe01_compatibility(client):
    response = client.post(
        "/api/feedback", json={"question": "Câu hỏi", "answer": "Câu trả lời", "vote": "up"}
    )
    assert response.status_code == 200
    assert response.get_json()["helpful"] is True


def test_not_found_is_json(client):
    assert_error(client.get("/api/not-found"), 404)


def test_wrong_method_is_json(client):
    assert_error(client.get("/api/chat"), 405)


def test_request_too_large_is_json(client):
    response = client.post(
        "/api/chat", data="x" * (17 * 1024), content_type="application/json"
    )
    assert_error(response, 413)


def test_cors_allows_local_frontend(client):
    response = client.options(
        "/api/chat",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
