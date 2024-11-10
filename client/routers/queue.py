from typing import List
from fastapi import APIRouter, HTTPException
from client.services.database import create_message, get_message, get_all_messages, delete_message

router = APIRouter()


# POST: Create a new message
@router.post("/message/", response_model=dict)
async def create_message_endpoint(message: dict):
    # Call the create_message function from the database service
    created_message = create_message(message)
    return {"message": "Message created successfully", "data": created_message}


# GET: Retrieve a message by ID
@router.get("/message/{message_id}", response_model=dict)
async def read_message(message_id: str):
    # Call the get_message function from the database service
    message = get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


# GET: Retrieve all messages
@router.get("/message/", response_model=List[dict])
async def read_messages():
    # Call the get_all_messages function from the database service
    return get_all_messages()


# DELETE: Delete a message by ID
@router.delete("/message/{message_id}", response_model=dict)
async def delete_message_endpoint(message_id: str):
    # Call the delete_message function from the database service
    if not delete_message(message_id):
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": f"Message with ID {message_id} deleted successfully"}
