"""Pytest configuration for bibliophage tests."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
import os

# Add the src directory to the Python path so we can import our modules
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

# Set required environment variables for config validation
# This prevents ValidationError when importing modules that use get_settings()
os.environ.setdefault("VECTOR_DB_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("DOC_DB_URL", "mongodb://test:test@localhost:27017/")


@pytest.fixture(autouse=True, scope="function")
def mock_database(monkeypatch):
    """Mock the database module to avoid requiring real database connections in tests.

    This fixture automatically mocks get_database() for all tests, providing a fake
    database repository with mock methods. Tests can still access the mock to verify
    calls or customize behavior.
    """
    # Create a mock database repository
    mock_db = MagicMock()

    # Mock all async methods with AsyncMock
    mock_db.store_pdf_document = AsyncMock(return_value="mock-pdf-id")
    mock_db.get_pdf_by_id = AsyncMock(return_value=None)
    mock_db.search_pdfs = AsyncMock(return_value=([], 0))
    mock_db.update_pdf_metadata = AsyncMock(return_value=True)

    mock_db.store_document = AsyncMock(return_value="mock-doc-id")
    mock_db.get_document_by_id = AsyncMock(return_value=None)
    mock_db.update_document = AsyncMock(return_value=None)
    mock_db.search_documents = AsyncMock(return_value=([], 0))
    mock_db.delete_document = AsyncMock(return_value=False)

    mock_db.initialize_indexes = AsyncMock()

    # Mock the get_database function to return our mock
    import database

    # Also reset the singleton state to ensure our mock is picked up
    database._database = None
    database._mongo_client = None

    # Mock the motor client creation to avoid actual DB connections
    mock_motor_client = MagicMock()
    monkeypatch.setattr("motor.motor_asyncio.AsyncIOMotorClient", lambda *args, **kwargs: mock_motor_client)

    # Return our mock database directly from get_database
    monkeypatch.setattr(database, "get_database", lambda: mock_db)

    return mock_db
