"""Tests for API routes: health, workflows. No writes to demo/ or real external calls."""
import pytest


def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "service" in data


def test_workflows_list_returns_200(client):
    r = client.get("/api/workflows")
    assert r.status_code == 200
    # Response is list of workflow summaries
    assert isinstance(r.json(), list)


def test_root_returns_service_info(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "service" in data
    assert "health" in data
