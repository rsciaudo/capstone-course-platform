"""
Contract-level tests for GET /api/health
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import SQLAlchemyError


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient):
    """GET /api/health reports ok when Postgres accepts a query."""
    response = await client.get("/api/health")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_unavailable_when_database_fails(client: AsyncClient, monkeypatch):
    """GET /api/health returns 503 when the database connection fails."""

    class BrokenConnection:
        async def __aenter__(self):
            raise SQLAlchemyError("down")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class BrokenEngine:
        def connect(self):
            return BrokenConnection()

    monkeypatch.setattr("app.main.engine", BrokenEngine())
    response = await client.get("/api/health")
    assert response.status_code == 503, response.text
    assert response.json() == {"status": "unavailable"}
