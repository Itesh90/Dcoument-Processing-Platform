"""
Pytest configuration and fixtures
"""
import pytest
from typing import Generator
from fastapi.testclient import TestClient

# Import your main app when available
# from api.main import app


@pytest.fixture(scope="session")
def test_db() -> Generator:
    """
    Create a test database
    """
    # Setup test database
    yield
    # Teardown test database


@pytest.fixture(scope="module")
def client() -> Generator:
    """
    Create a test client
    """
    # Uncomment when app is available
    # with TestClient(app) as test_client:
    #     yield test_client
    yield None
