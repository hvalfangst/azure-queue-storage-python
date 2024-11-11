import json
from typing import List, Optional

from azure.core.exceptions import AzureError
from azure.storage.queue import QueueClient
from fastapi import APIRouter, HTTPException

from client.config import config
from client.logger import logger
from client.models import Person
from client.models.message import Message, UpdateMessageResponse, UpdateMessageRequest
from client.models.messages import Messages

router = APIRouter()


# POST: Create a new message and add it to the queue
@router.post("/messages", response_model=Message)
async def create_message_endpoint(person: Person):
    """
    This endpoint allows you to send a new message to an Azure Queue. The message is added to the queue in the order
    it was received (FIFO - First In, First Out).


    When a message is successfully added to the queue, it returns the message's details, such as the message ID,
    content, insertion time, expiration time, and pop receipt.

    :param person:
        The content of the message to be added to the queue. It is expected to be a dictionary, which will be serialized
        into the message content to be sent to the Azure Queue.

    :returns:
        A `QueueMessageResponseModel` instance containing the details of the message that was added to the queue,
        such as the message's content, ID, insertion time, expiration time, and pop receipt.

    """
    try:
        # Initialize the QueueClient
        queue_client: QueueClient = QueueClient.from_connection_string(config.CONNECTION_STRING, config.QUEUE_NAME)

        # Serialize the message as JSON string
        message_content = person.json()

        # Send the message to the queue
        raw_results: Message = queue_client.send_message(message_content)

        # Log the raw queue message for debugging
        logger.info(f"Raw QueueMessage: {raw_results}")

        # Map the QueueMessage properties to the QueueMessageModel
        response = Message(
            message_content=person,
            message_id=raw_results.id,
            insertion_time=raw_results.inserted_on,
            expiration_time=raw_results.expires_on,
            pop_receipt=raw_results.pop_receipt,
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# GET: Retrieve and delete a message from the queue
@router.get("/messages/pop", response_model=dict)
async def pop_message():
    """
    This endpoint retrieves the next message from an Azure Queue and deletes it immediately after retrieval. It
    follows a **First-In-First-Out (FIFO)** order, meaning the first message added is the first one to be processed.

    If the queue is **empty**, a message indicating "No messages in the queue" is returned.

    If the queue is **not
    empty**, meaning that there is a message in the queue, it is retrieved, parsed, and deleted based on the
    **pop_receipt** contained in the response.

     :returns:
        A dictionary containing the status message and, if a message is retrieved, the message's details such as
        its content, ID, insertion time, expiration time, and pop receipt. If no messages are available, the response
        will include a message indicating the queue is empty.
    """
    try:
        # Initialize the QueueClient
        queue_client = QueueClient.from_connection_string(config.CONNECTION_STRING, config.QUEUE_NAME)

        # Retrieve the next message from the queue
        queue_message: Optional[Message] = queue_client.receive_message(visibility_timeout=60)

        # Check if a message was retrieved
        if queue_message is None:
            return {"message": "No messages in the queue"}

        try:
            person = Person.parse_raw(queue_message.content)
        except json.JSONDecodeError:
            person = Person(
                first_name="Unknown", last_name="Unknown", age=0, occupation="Unknown", location="Unknown"
            )

        # Immediately delete (pop from queue) the message after retrieval based on message "pop_receipt"
        queue_client.delete_message(queue_message.id, queue_message.pop_receipt)

        # Prepare the response
        response = Message(
            message_content=person,
            message_id=queue_message.id,
            insertion_time=queue_message.inserted_on,
            expiration_time=queue_message.expires_on,
            pop_receipt=queue_message.pop_receipt,
        )

        return {"message": "Message retrieved and deleted from queue", "data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/messages", response_model=Messages)
async def read_messages(
        messages_per_page: int = 5,
        visibility_timeout: int = 30,
        max_messages: Optional[int] = 10
):
    """
    This endpoint retrieves a list of messages from an Azure Queue with pagination support.
    It allows you to specify the number of messages per page and the visibility timeout.
    The retrieved messages are parsed and returned with their content, IDs, insertion, and expiration times.

    :param messages_per_page:
        The number of messages to retrieve per page. Default is 5.
    :param visibility_timeout:
        Time in seconds that the retrieved messages will remain invisible to other consumers after being retrieved.
        Default is 30 seconds.
    :param max_messages:
        The maximum number of messages to retrieve. This value must be between 1 and 32. Default is 10.

    :returns:
        A `QueueMessagesResponseModel` instance containing the list of messages with their details.
    """
    try:
        # Initialize the QueueClient
        queue_client = QueueClient.from_connection_string(config.CONNECTION_STRING, config.QUEUE_NAME)

        # Retrieve messages using pagination
        message_iterator = queue_client.receive_messages(
            messages_per_page=messages_per_page,
            visibility_timeout=visibility_timeout,
            max_messages=max_messages
        )

        messages: List[Message] = []
        for queue_message in message_iterator:
            try:
                logger.info(f"Peeked message content: {queue_message.content}")
                person = Person.parse_raw(queue_message.content)
            except json.JSONDecodeError:
                person = Person(
                    first_name="Unknown", last_name="Unknown", age=0, occupation="Unknown", location="Unknown")

            # Append the message to the list
            messages.append(Message(
                message_id=queue_message.id,
                insertion_time=queue_message.inserted_on.isoformat(),
                expiration_time=queue_message.expires_on.isoformat(),
                pop_receipt=queue_message.pop_receipt,
                message_content=person
            ))

        return Messages(messages=messages)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/messages/peek", response_model=Messages)
async def peek_messages(max_messages: Optional[int] = 10):
    """
   Retrieves messages from the front of the queue without altering their visibility or removing them.
   This operation allows you to view messages while they remain in the queue, making it ideal for
   monitoring or inspecting the queue's contents without modifying the queue itself.
   Unlike reading messages, peeking does not change their state in the queue or affect their processing time.

    :param max_messages:
        The number of messages to peek (up to a maximum of 32). Default is 10. This value determines how many
        messages will be retrieved for inspection without affecting the queue.

    :returns:
        A `QueueMessagesResponseModel` instance containing a list of the peeked messages, including their content,
        IDs, insertion time, and expiration time.

   """
    try:
        queue_client = QueueClient.from_connection_string(config.CONNECTION_STRING, config.QUEUE_NAME)

        # Retrieve messages without modifying visibility
        peeked_messages = queue_client.peek_messages(max_messages=max_messages)

        messages: List[Message] = []
        for queue_message in peeked_messages:
            try:
                logger.info(f"Peeked message content: {queue_message.content}")
                person = Person.parse_raw(queue_message.content)
            except json.JSONDecodeError:
                person = Person(
                    first_name="Unknown", last_name="Unknown", age=0, occupation="Unknown", location="Unknown"
                )

            # Append the message to the list
            messages.append(Message(
                message_id=queue_message.id,
                insertion_time=queue_message.inserted_on.isoformat(),
                expiration_time=queue_message.expires_on.isoformat(),
                pop_receipt=getattr(queue_message, 'pop_receipt', None),
                message_content=person
            ))

        return Messages(messages=messages)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.put("/messages/{message_id}", response_model=UpdateMessageResponse)
async def update_message(message_id: str, request: UpdateMessageRequest):
    """
    Updates the visibility timeout of a message and optionally updates its content.
    If the message needs more processing time, this extends its invisibility period in the queue.

    :param message_id:
        The unique identifier of the message to be updated. This ID is specified in the URL path.

   :param request: The request body that contains the details to update the message. The body should include:
        - `pop_receipt`: A receipt that is returned when the message is retrieved. This is required to identify the message for updating or deleting purposes, and ensures that the message is not modified by other consumers while it is being updated.
        - `content`: The new content for the message. If not provided, the content remains unchanged. Default is `None`.
        - `visibility_timeout`: The time, in seconds, to extend the message's invisibility in the queue. This prevents other consumers from retrieving and processing the message before the specified timeout. Default is 30 seconds.

    :returns:
        An `UpdateMessageResponseModel` instance containing the updated message's details, including the message ID,
        pop receipt, next visibility time, and content.

    """
    try:
        # Log the actual incoming request data
        logger.info(f"Received request to update message {message_id}: {request.dict()}")

        queue_client: QueueClient = QueueClient.from_connection_string(config.CONNECTION_STRING, config.QUEUE_NAME)

        # Update the message visibility timeout and content if necessary
        updated_message = queue_client.update_message(
            message=message_id,
            pop_receipt=request.pop_receipt,
            content=request.content,
            visibility_timeout=request.visibility_timeout
        )

        # Log updated message details
        logger.info(
            f"Message with ID {message_id} updated successfully. New visibility time: {updated_message.next_visible_on}")

        # Return updated message details
        return UpdateMessageResponse(
            message_id=updated_message.id,
            pop_receipt=updated_message.pop_receipt,
            next_visible_on=updated_message.next_visible_on.isoformat(),
            message_content=request.content
        )

    # Handle Azure specific errors
    except AzureError as e:
        if 'MessageNotFound' in str(e):
            logger.error(f"Azure error: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Message with ID {message_id} was not found.")
        else:  # Misc Azure errors
            logger.error(f"Azure error: {str(e)}")
            raise HTTPException(status_code=500, detail="An internal error occurred with Azure.")
    # Generic errors
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.delete("/messages")
async def clear_messages():
    """
    Deletes all messages from the queue.
    """
    try:
        queue_client = QueueClient.from_connection_string(config.CONNECTION_STRING, config.QUEUE_NAME)

        # Clear the queue without bothering to check if it is empty (don't wasted cycles)
        queue_client.clear_messages()

        return {"message": "All messages cleared from the queue."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
