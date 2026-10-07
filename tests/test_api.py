import pytest

from app import MAX_MESSAGE_LENGTH, create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    return app.test_client()


def new_conversation(client):
    return client.post("/api/conversations").get_json()["id"]


def send(client, cid, payload):
    return client.post(f"/api/conversations/{cid}/messages", json=payload)


def test_start_conversation(client):
    res = client.post("/api/conversations")
    assert res.status_code == 201
    assert res.get_json()["id"] == 1


def test_send_message_returns_bot_reply(client):
    cid = new_conversation(client)
    res = send(client, cid, {"message": "Hello"})
    body = res.get_json()
    assert res.status_code == 201
    assert body["user_message"]["content"] == "Hello"
    assert body["bot_message"]["content"] == "Hello! How can I help you?"


def test_history_is_stored_in_order(client):
    cid = new_conversation(client)
    send(client, cid, {"message": "Hello"})
    send(client, cid, {"message": "What is Python?"})
    messages = client.get(f"/api/conversations/{cid}").get_json()["messages"]
    assert [m["role"] for m in messages] == ["user", "bot", "user", "bot"]
    assert messages[2]["content"] == "What is Python?"


def test_bot_uses_conversation_history(client):
    cid = new_conversation(client)
    send(client, cid, {"message": "My name is Ravi"})
    res = send(client, cid, {"message": "What is my name?"})
    assert "Ravi" in res.get_json()["bot_message"]["content"]


def test_conversations_are_separate(client):
    a, b = new_conversation(client), new_conversation(client)
    send(client, a, {"message": "Hello"})
    assert client.get(f"/api/conversations/{b}").get_json()["messages"] == []


@pytest.mark.parametrize("payload", [
    {"message": ""}, {"message": "   "}, {"message": 123},
    {"message": None}, {}, [], "text",
])
def test_invalid_messages_rejected(client, payload):
    cid = new_conversation(client)
    assert send(client, cid, payload).status_code == 400


def test_non_json_body_rejected(client):
    cid = new_conversation(client)
    res = client.post(f"/api/conversations/{cid}/messages", data="hi")
    assert res.status_code == 400


def test_too_long_message_rejected(client):
    cid = new_conversation(client)
    res = send(client, cid, {"message": "a" * (MAX_MESSAGE_LENGTH + 1)})
    assert res.status_code == 400


def test_rejected_message_is_not_saved(client):
    cid = new_conversation(client)
    send(client, cid, {"message": ""})
    assert client.get(f"/api/conversations/{cid}").get_json()["messages"] == []


def test_unknown_conversation_returns_404(client):
    assert client.get("/api/conversations/999").status_code == 404
    assert send(client, 999, {"message": "Hello"}).status_code == 404


def test_bot_remembers_context_from_earlier_messages(client):
    cid = new_conversation(client)
    send(client, cid, {"message": "My dog's name is Bruno"})
    send(client, cid, {"message": "The meeting is at 5 PM"})
    dog = send(client, cid, {"message": "What is my dog's name?"}).get_json()
    meeting = send(client, cid, {"message": "When is the meeting?"}).get_json()
    assert "Bruno" in dog["bot_message"]["content"]
    assert "5 PM" in meeting["bot_message"]["content"]


def test_context_does_not_leak_between_conversations(client):
    a, b = new_conversation(client), new_conversation(client)
    send(client, a, {"message": "My name is Ravi"})
    res = send(client, b, {"message": "What is my name?"}).get_json()
    assert "haven't told me" in res["bot_message"]["content"]
