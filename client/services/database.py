from typing import List, Optional

# In-memory storage using dictionary
messages_db = {}


def create_message(message: dict) -> dict:
    """Create a new message and return the created message with an assigned ID."""
    # Generate a new message ID based on the size of our dictionary data structure
    message_id = str(len(messages_db) + 1)
    message["message_id"] = message_id  # Add the message_id to the message data
    messages_db[message_id] = message  # Store the message in the in-memory dictionary
    return message


def get_message(message_id: str) -> Optional[dict]:
    """Retrieve a message by its ID."""
    return messages_db.get(message_id)


def get_all_messages() -> List[dict]:
    """Retrieve all messages."""
    return list(messages_db.values())


def delete_message(message_id: str) -> bool:
    """Delete a message by its ID."""
    if message_id in messages_db:
        del messages_db[message_id]
        return True
    return False
