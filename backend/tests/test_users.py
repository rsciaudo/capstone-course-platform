"""
Contract-level tests for the /api/users endpoints.

These routes are public. Tests lock that contract in, including the cases
that should succeed without a session.
"""

import pytest
from httpx import AsyncClient

from tests.helpers import (
    MISSING_ID,
    PASSWORD,
    assert_error,
    assert_user_shape,
)


# GET /api/users


@pytest.mark.asyncio
async def test_list_users_is_public(client: AsyncClient, world):
    """GET /api/users does not require a session."""
    response = await client.get("/api/users")
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, list)
    usernames = {user["username"] for user in body}
    assert world.admin.username in usernames
    assert world.student.username in usernames
    for user in body:
        assert_user_shape(user)


@pytest.mark.asyncio
async def test_list_users_filters_by_group(client: AsyncClient, world):
    """GET /api/users?group_id returns only members of that group."""
    response = await client.get("/api/users", params={"group_id": world.group_id})
    assert response.status_code == 200, response.text
    usernames = {user["username"] for user in response.json()}
    assert usernames == {
        world.educator.username,
        world.other_educator.username,
        world.student.username,
        world.other_student.username,
    }


@pytest.mark.asyncio
async def test_list_users_unknown_group_is_empty(client: AsyncClient):
    """GET /api/users?group_id for a missing group is an empty list."""
    response = await client.get("/api/users", params={"group_id": MISSING_ID})
    assert response.status_code == 200, response.text
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_users_rejects_bad_group_id(client: AsyncClient):
    """GET /api/users rejects a non-integer group_id."""
    response = await client.get("/api/users", params={"group_id": "abc"})
    assert response.status_code == 422, response.text


# GET /api/users/{user_id}


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, world):
    """GET /api/users/{id} returns one user."""
    response = await client.get(f"/api/users/{world.student.id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert_user_shape(body)
    assert body["id"] == world.student.id
    assert body["role"] == "student"
    assert body["group_id"] == world.group_id


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    """GET /api/users/{id} returns 404 for a missing user."""
    response = await client.get(f"/api/users/{MISSING_ID}")
    assert_error(response, 404, "User not found")


@pytest.mark.asyncio
async def test_get_user_rejects_string_id(client: AsyncClient):
    """GET /api/users/{id} rejects a non-integer id."""
    response = await client.get("/api/users/nope")
    assert response.status_code == 422, response.text


# POST /api/users


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, world):
    """POST /api/users creates a student and omits the password."""
    response = await client.post(
        "/api/users",
        json={
            "name": "  Ada Lovelace  ",
            "username": "  ada  ",
            "password": PASSWORD,
            "role": "student",
            "group_id": world.group_id,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert_user_shape(body)
    assert body["name"] == "Ada Lovelace"
    assert body["username"] == "ada"
    assert body["role"] == "student"
    assert body["group_id"] == world.group_id


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client: AsyncClient, world):
    """POST /api/users rejects a username that already exists."""
    response = await client.post(
        "/api/users",
        json={
            "name": "Second Admin",
            "username": world.admin.username,
            "password": PASSWORD,
            "role": "admin",
        },
    )
    assert_error(response, 409, "User could not be saved")


@pytest.mark.asyncio
async def test_create_grouped_role_without_group(client: AsyncClient):
    """POST /api/users rejects an educator or student with no group."""
    response = await client.post(
        "/api/users",
        json={
            "name": "No Group",
            "username": "no-group",
            "password": PASSWORD,
            "role": "educator",
        },
    )
    assert response.status_code == 422, response.text
    assert "educator and student require a group_id" in response.text


@pytest.mark.asyncio
async def test_create_ungrouped_role_with_group(client: AsyncClient, world):
    """POST /api/users rejects an admin or super-user assigned to a group."""
    response = await client.post(
        "/api/users",
        json={
            "name": "Grouped Admin",
            "username": "grouped-admin",
            "password": PASSWORD,
            "role": "admin",
            "group_id": world.group_id,
        },
    )
    assert response.status_code == 422, response.text
    assert "super-user and admin must not have a group_id" in response.text


@pytest.mark.asyncio
async def test_create_user_unknown_group(client: AsyncClient):
    """POST /api/users returns 409 when group_id does not exist."""
    response = await client.post(
        "/api/users",
        json={
            "name": "Lost Student",
            "username": "lost-student",
            "password": PASSWORD,
            "role": "student",
            "group_id": MISSING_ID,
        },
    )
    assert_error(response, 409, "User could not be saved")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {
            "name": "   ",
            "username": "blank-name",
            "password": PASSWORD,
            "role": "admin",
        },
        {
            "name": "Blank User",
            "username": "   ",
            "password": PASSWORD,
            "role": "admin",
        },
        {"name": "No Password", "username": "no-password", "password": "", "role": "admin"},
        {
            "name": "Bad Role",
            "username": "bad-role",
            "password": PASSWORD,
            "role": "teacher",
        },
    ],
)
async def test_create_user_rejects_invalid_body(client: AsyncClient, payload):
    """POST /api/users rejects blank fields and unknown roles."""
    response = await client.post("/api/users", json=payload)
    assert response.status_code == 422, response.text


# PATCH /api/users/{user_id}


@pytest.mark.asyncio
async def test_update_user_name(client: AsyncClient, world):
    """PATCH /api/users/{id} updates the name and strips whitespace."""
    response = await client.patch(
        f"/api/users/{world.other_student.id}",
        json={"name": "  Renamed Student  "},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert_user_shape(body)
    assert body["name"] == "Renamed Student"
    assert body["role"] == "student"


@pytest.mark.asyncio
async def test_update_user_empty_body(client: AsyncClient, world):
    """PATCH /api/users/{id} with no fields leaves the user unchanged."""
    response = await client.patch(f"/api/users/{world.student.id}", json={})
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Student"


@pytest.mark.asyncio
async def test_update_user_promotes_student_when_group_is_cleared(
    client: AsyncClient, world
):
    """PATCH /api/users/{id} can make a student an admin by clearing group_id."""
    response = await client.patch(
        f"/api/users/{world.other_student.id}",
        json={"role": "admin", "group_id": None},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["role"] == "admin"
    assert body["group_id"] is None


@pytest.mark.asyncio
async def test_update_user_rejects_admin_who_keeps_a_group(client: AsyncClient, world):
    """PATCH /api/users/{id} rejects an admin role while group_id is still set."""
    response = await client.patch(
        f"/api/users/{world.student.id}",
        json={"role": "admin"},
    )
    assert_error(response, 422, "super-user and admin must not have a group_id")


@pytest.mark.asyncio
async def test_update_user_rejects_clearing_student_group(client: AsyncClient, world):
    """PATCH /api/users/{id} rejects a student with no group."""
    response = await client.patch(
        f"/api/users/{world.student.id}",
        json={"group_id": None},
    )
    assert_error(response, 422, "educator and student require a group_id")


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient):
    """PATCH /api/users/{id} returns 404 for a missing user."""
    response = await client.patch(f"/api/users/{MISSING_ID}", json={"name": "Nope"})
    assert_error(response, 404, "User not found")


@pytest.mark.asyncio
async def test_update_user_rejects_blank_name(client: AsyncClient, world):
    """PATCH /api/users/{id} rejects a blank name."""
    response = await client.patch(f"/api/users/{world.student.id}", json={"name": "   "})
    assert response.status_code == 422, response.text


# DELETE /api/users/{user_id}


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, world):
    """DELETE /api/users/{id} removes a user who is not referenced."""
    response = await client.delete(f"/api/users/{world.other_student.id}")
    assert response.status_code == 204, response.text
    follow = await client.get(f"/api/users/{world.other_student.id}")
    assert_error(follow, 404, "User not found")


@pytest.mark.asyncio
async def test_delete_user_still_referenced(client: AsyncClient, world):
    """DELETE /api/users/{id} returns 409 when another row points at the user."""
    response = await client.delete(f"/api/users/{world.admin.id}")
    assert_error(response, 409, "User is still referenced by another record")
    follow = await client.get(f"/api/users/{world.admin.id}")
    assert follow.status_code == 200, follow.text


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient):
    """DELETE /api/users/{id} returns 404 for a missing user."""
    response = await client.delete(f"/api/users/{MISSING_ID}")
    assert_error(response, 404, "User not found")
