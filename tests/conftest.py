"""
Shared fixtures for the test suite.

Environment variables are set before any application module is imported so that
the module-level `config = initialize()` in `client.config.storage_account`
succeeds without a real `.env` file.
"""
import os

# Must happen before the FastAPI app (and therefore the config module) is imported.
# This is the well-known default Azure Storage Emulator (Azurite) connection string
# — it contains no real credentials and is safe to use in tests.
os.environ.setdefault("CONNECTION_STRING", "DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;")
os.environ.setdefault("QUEUE_NAME", "test-queue")

import pytest
from fastapi.testclient import TestClient
from client.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
