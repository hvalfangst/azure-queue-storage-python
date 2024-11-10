from typing import List
from fastapi import APIRouter, HTTPException

router = APIRouter()

# In-memory storage using dictionary
messages_db = {}


# POST: Create a new message
@router.post("/message/", response_model=dict)
async def create_message(message: dict):
    # Generate a new message ID based on the size of our dictionary data structure
    message_id = str(len(messages_db) + 1)
    message["message_id"] = message_id  # Add the message_id to the message data
    messages_db[message_id] = message  # Store the message in the in-memory dictionary
    return {"message": "Message created successfully", "data": message}


# GET: Retrieve a message by ID
@router.get("/message/{message_id}", response_model=dict)
async def read_message(message_id: str):
    # Check if the message exists in memory
    if message_id not in messages_db:
        raise HTTPException(status_code=404, detail="Message not found")
    return messages_db[message_id]


# GET: Retrieve all messages
@router.get("/message/", response_model=List[dict])
async def read_messages():
    # Return all messages stored in memory
    return list(messages_db.values())


# DELETE: Delete a message by ID
@router.delete("/message/{message_id}", response_model=dict)
async def delete_message(message_id: str):
    # Check if the message exists in memory
    if message_id not in messages_db:
        raise HTTPException(status_code=404, detail="Message not found")
    # Delete the message from memory
    del messages_db[message_id]
    return {"message": f"Message with ID {message_id} deleted successfully"}
