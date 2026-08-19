"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

# Force Ollama fallback in tests (skip cloud APIs)
os.environ["CEREBRAS_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["TOGETHER_API_KEY"] = ""
os.environ["APP_ENV"] = "testing"


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from backend.app.main import app
    with TestClient(app) as c:
        yield c
