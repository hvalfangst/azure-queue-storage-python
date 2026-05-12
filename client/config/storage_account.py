from fastapi import HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict
from client.logger import logger


class StorageAccountConfiguration(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="client/storage_account_config.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    CONNECTION_STRING: str
    QUEUE_NAME: str


def initialize():
    try:
        settings = StorageAccountConfiguration()
        logger.info("Configuration values loaded successfully.")
        return settings
    except Exception as e:
        logger.critical(f"Error loading config: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")


# Initialize StorageAccountConfiguration
config = initialize()
