"""Tests for all /queue/* endpoints with a mocked Azure QueueClient."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INSERTED_ON = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
EXPIRES_ON = datetime(2024, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
NEXT_VISIBLE_ON = datetime(2024, 6, 1, 12, 0, 30, tzinfo=timezone.utc)

PERSON_PAYLOAD = {
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "occupation": "Engineer",
    "location": "Oslo",
}


def _make_queue_message(
    msg_id: str = "msg-001",
    content: str | None = None,
    pop_receipt: str = "receipt-abc",
) -> MagicMock:
    """Return a mock object that resembles an Azure SDK QueueMessage."""
    if content is None:
        content = json.dumps(PERSON_PAYLOAD)
    msg = MagicMock()
    msg.id = msg_id
    msg.content = content
    msg.inserted_on = INSERTED_ON
    msg.expires_on = EXPIRES_ON
    msg.pop_receipt = pop_receipt
    msg.next_visible_on = NEXT_VISIBLE_ON
    return msg


def _make_updated_message(
    msg_id: str = "msg-001",
    pop_receipt: str = "new-receipt",
) -> MagicMock:
    """Return a mock object that resembles an Azure SDK UpdatedMessage."""
    msg = MagicMock()
    msg.id = msg_id
    msg.pop_receipt = pop_receipt
    msg.next_visible_on = NEXT_VISIBLE_ON
    return msg


# ---------------------------------------------------------------------------
# POST /queue/messages
# ---------------------------------------------------------------------------

class TestCreateMessage:
    def test_create_message_success(self, client):
        mock_msg = _make_queue_message()

        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.send_message.return_value = mock_msg

            response = client.post("/queue/messages", json=PERSON_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        assert data["message_id"] == "msg-001"
        assert data["pop_receipt"] == "receipt-abc"
        assert data["message_content"]["first_name"] == "John"

    def test_create_message_azure_error(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.send_message.side_effect = Exception("connection refused")

            response = client.post("/queue/messages", json=PERSON_PAYLOAD)

        assert response.status_code == 500
        assert "connection refused" in response.json()["detail"]

    def test_create_message_invalid_payload(self, client):
        response = client.post("/queue/messages", json={"first_name": "only"})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /queue/messages/pop
# ---------------------------------------------------------------------------

class TestPopMessage:
    def test_pop_returns_message(self, client):
        mock_msg = _make_queue_message()

        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.receive_message.return_value = mock_msg

            response = client.get("/queue/messages/pop")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Message retrieved and deleted from queue"
        assert data["data"]["message_id"] == "msg-001"
        instance.delete_message.assert_called_once_with("msg-001", "receipt-abc")

    def test_pop_empty_queue(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.receive_message.return_value = None

            response = client.get("/queue/messages/pop")

        assert response.status_code == 200
        assert response.json() == {"message": "No messages in the queue"}

    def test_pop_invalid_json_content(self, client):
        mock_msg = _make_queue_message(content="not-valid-json")

        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.receive_message.return_value = mock_msg

            response = client.get("/queue/messages/pop")

        assert response.status_code == 200
        data = response.json()
        # Falls back to Unknown person
        assert data["data"]["message_content"]["first_name"] == "Unknown"

    def test_pop_azure_error(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.receive_message.side_effect = Exception("queue not found")

            response = client.get("/queue/messages/pop")

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /queue/messages
# ---------------------------------------------------------------------------

class TestReadMessages:
    def test_read_messages_returns_list(self, client):
        msgs = [_make_queue_message(f"msg-{i:03d}") for i in range(3)]

        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.receive_messages.return_value = iter(msgs)

            response = client.get("/queue/messages")

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 3
        assert data["messages"][0]["message_id"] == "msg-000"

    def test_read_messages_empty_queue(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.receive_messages.return_value = iter([])

            response = client.get("/queue/messages")

        assert response.status_code == 200
        assert response.json()["messages"] == []

    def test_read_messages_custom_params(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.receive_messages.return_value = iter([])

            client.get("/queue/messages?messages_per_page=2&visibility_timeout=60&max_messages=5")

        instance.receive_messages.assert_called_once_with(
            messages_per_page=2,
            visibility_timeout=60,
            max_messages=5,
        )

    def test_read_messages_azure_error(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.receive_messages.side_effect = Exception("service unavailable")

            response = client.get("/queue/messages")

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /queue/messages/peek
# ---------------------------------------------------------------------------

class TestPeekMessages:
    def test_peek_returns_messages(self, client):
        msgs = [_make_queue_message(f"msg-{i:03d}", pop_receipt=None) for i in range(2)]
        for m in msgs:
            m.pop_receipt = None

        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.peek_messages.return_value = msgs

            response = client.get("/queue/messages/peek")

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2

    def test_peek_empty_queue(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.peek_messages.return_value = []

            response = client.get("/queue/messages/peek")

        assert response.status_code == 200
        assert response.json()["messages"] == []

    def test_peek_azure_error(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.peek_messages.side_effect = Exception("timeout")

            response = client.get("/queue/messages/peek")

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# PUT /queue/messages/{message_id}
# ---------------------------------------------------------------------------

class TestUpdateMessage:
    UPDATE_BODY = {
        "pop_receipt": "old-receipt",
        "content": PERSON_PAYLOAD,
        "visibility_timeout": 60,
    }

    def test_update_message_success(self, client):
        mock_updated = _make_updated_message()

        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.update_message.return_value = mock_updated

            response = client.put("/queue/messages/msg-001", json=self.UPDATE_BODY)

        assert response.status_code == 200
        data = response.json()
        assert data["message_id"] == "msg-001"
        assert data["pop_receipt"] == "new-receipt"

    def test_update_message_not_found(self, client):
        from azure.core.exceptions import AzureError

        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.update_message.side_effect = AzureError("MessageNotFound")

            response = client.put("/queue/messages/msg-999", json=self.UPDATE_BODY)

        assert response.status_code == 404

    def test_update_message_azure_error(self, client):
        from azure.core.exceptions import AzureError

        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.update_message.side_effect = AzureError("InternalError")

            response = client.put("/queue/messages/msg-001", json=self.UPDATE_BODY)

        assert response.status_code == 500

    def test_update_message_unexpected_error(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.update_message.side_effect = RuntimeError("unexpected")

            response = client.put("/queue/messages/msg-001", json=self.UPDATE_BODY)

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /queue/messages
# ---------------------------------------------------------------------------

class TestClearMessages:
    def test_clear_messages_success(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value

            response = client.delete("/queue/messages")

        assert response.status_code == 200
        assert response.json() == {"message": "All messages cleared from the queue."}
        instance.clear_messages.assert_called_once()

    def test_clear_messages_azure_error(self, client):
        with patch("client.routers.queue.QueueClient") as MockQC:
            instance = MockQC.from_connection_string.return_value
            instance.clear_messages.side_effect = Exception("permission denied")

            response = client.delete("/queue/messages")

        assert response.status_code == 500
