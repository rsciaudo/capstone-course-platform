"""
Contract-level tests for the /api/auth endpoints
"""

import pytest
from httpx import AsyncClient

from tests.helpers import PASSWORD, assert_error, assert_user_shape, login


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, world):
    """POST /api/auth/login returns the user and a session cookie."""
    response = await client.post(
        "/api/auth/login",
        json={"username": world.admin.username, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert_user_shape(body)
    assert body["username"] == world.admin.username
    assert body["role"] == "admin"
    assert body["group_id"] is None
    assert "session" in response.cookies or "session" in client.cookies


@pytest.mark.asyncio
async def test_login_strips_username(client: AsyncClient, world):
    """POST /api/auth/login accepts surrounding whitespace on the username."""
    response = await client.post(
        "/api/auth/login",
        json={"username": f"  {world.student.username}  ", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    assert response.json()["username"] == world.student.username


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    """POST /api/auth/login rejects an unknown username."""
    response = await client.post(
        "/api/auth/login",
        json={"username": "missing", "password": PASSWORD},
    )
    assert_error(response, 401, "Invalid username or password")


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, world):
    """POST /api/auth/login rejects a wrong password with the same error."""
    response = await client.post(
        "/api/auth/login",
        json={"username": world.admin.username, "password": "wrong-password"},
    )
    assert_error(response, 401, "Invalid username or password")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"username": "", "password": PASSWORD},
        {"username": "   ", "password": PASSWORD},
        {"username": "admin", "password": ""},
        {"password": PASSWORD},
        {"username": "admin"},
    ],
)
async def test_login_rejects_blank_fields(client: AsyncClient, payload):
    """POST /api/auth/login rejects missing or blank credentials."""
    response = await client.post("/api/auth/login", json=payload)
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_logout_clears_session(client: AsyncClient, world):
    """POST /api/auth/logout ends the session."""
    cookies = await login(client, world.student.username)
    response = await client.post("/api/auth/logout", cookies=cookies)
    assert response.status_code == 204, response.text
    assert "session=" in response.headers.get("set-cookie", "").lower()
    # The session is the cookie. Logout replaces it, and the replacement does not authenticate.
    replacement = {key: value for key, value in response.cookies.items()}
    me = await client.get("/api/auth/me", cookies=replacement)
    assert_error(me, 401, "Not authenticated")


@pytest.mark.asyncio
async def test_logout_without_session(client: AsyncClient):
    """POST /api/auth/logout succeeds when no one is logged in."""
    response = await client.post("/api/auth/logout")
    assert response.status_code == 204, response.text


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    """GET /api/auth/me requires a session."""
    response = await client.get("/api/auth/me")
    assert_error(response, 401, "Not authenticated")


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient, world, educator_cookies):
    """GET /api/auth/me returns the logged-in user."""
    response = await client.get("/api/auth/me", cookies=educator_cookies)
    assert response.status_code == 200, response.text
    body = response.json()
    assert_user_shape(body)
    assert body["id"] == world.educator.id
    assert body["role"] == "educator"
    assert body["group_id"] == world.group_id


@pytest.mark.asyncio
async def test_me_rejects_deleted_user(client: AsyncClient, world):
    """GET /api/auth/me rejects a session whose user was deleted."""
    cookies = await login(client, world.other_student.username)
    deleted = await client.delete(f"/api/users/{world.other_student.id}")
    assert deleted.status_code == 204, deleted.text
    response = await client.get("/api/auth/me", cookies=cookies)
    assert_error(response, 401, "Not authenticated")
