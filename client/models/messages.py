from typing import List
from pydantic import BaseModel
from client.models import Message


class Messages(BaseModel):
    messages: List[Message]
