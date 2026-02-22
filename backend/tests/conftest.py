"""Pytest configuration. Set mock modes before app loads so tests don't call real APIs."""
import os

import pytest

# Must set before any app import so settings load with mock
os.environ.setdefault("NOVA_MODE", "mock")
os.environ.setdefault("NOVA_ACT_MODE", "mock")

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
