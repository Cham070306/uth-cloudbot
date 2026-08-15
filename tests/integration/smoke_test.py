"""
Smoke test - chạy với BASE_URL=https://uth-cloudbot.onrender.com
Usage: BASE_URL=https://uth-cloudbot.onrender.com pytest tests/integration/smoke_test.py -v
"""
import os
import requests
import pytest

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8080").rstrip("/")


def test_health():
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chat_lich_hoc():
    r = requests.post(f"{BASE_URL}/api/chat", json={"message": "lich hoc"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "intent" in data


def test_chat_hoc_phi():
    r = requests.post(f"{BASE_URL}/api/chat", json={"message": "hoc phi"})
    assert r.status_code == 200
    assert "answer" in r.json()


def test_chat_invalid():
    r = requests.post(f"{BASE_URL}/api/chat", json={"message": ""})
    assert r.status_code in [400, 422]


def test_feedback():
    r = requests.post(f"{BASE_URL}/api/feedback", json={
        "message_id": "msg-test-001",
        "rating": "up"
    })
    assert r.status_code == 200