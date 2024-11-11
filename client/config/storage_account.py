from dotenv import load_dotenv
from fastapi import HTTPException
from pydantic_settings import BaseSettings
from client.logger import logger

load_dotenv()


class StorageAccountConfiguration(BaseSettings):
    CONNECTION_STRING: str
    QUEUE_NAME: str

    class Config:
        env_file = "client/storage_account_config.env"


def initialize():
    try:
        # Create an instance of StorageAccountConfiguration
        settings = StorageAccountConfiguration()

        # Check if the connection string field is set
        if not settings.CONNECTION_STRING:
            logger.error("Connection string is missing from .env file")
            raise HTTPException(status_code=500, detail="Connection string is missing from .env file")

        # Check if the queue name field is set
        if not settings.QUEUE_NAME:
            logger.error("Queue name is missing from .env file")
            raise HTTPException(status_code=500, detail="Queue name is missing from .env file")

        logger.info("Configuration values loaded successfully.")
        return settings
    except FileNotFoundError:
        logger.critical("local_config.env file not found in client directory.")
        raise HTTPException(status_code=500, detail="local_config.env file not found in client directory.")
    except Exception as e:
        logger.critical(f"Error loading config: {e}")
        raise HTTPException(status_code=500, detail="Configuration error")


# Initialize StorageAccountConfiguration
config = initialize()
