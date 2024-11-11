from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from client.models import Person


class Message(BaseModel):
    message_content: Person
    message_id: str
    insertion_time: datetime
    expiration_time: datetime
    pop_receipt: Optional[str] = None


class UpdateMessageResponse(BaseModel):
    message_id: str
    pop_receipt: str
    next_visible_on: str
    message_content: Optional[dict] = None


class UpdateMessageRequest(BaseModel):
    pop_receipt: str
    content: Person
    visibility_timeout: Optional[int] = 30
