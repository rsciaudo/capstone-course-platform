"""
Contract-level tests for the /api/edit-grants endpoints
"""

import pytest
from httpx import AsyncClient

from tests.helpers import MISSING_ID, assert_error, assert_grant_shape


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/edit-grants", None),
        ("POST", "/api/edit-grants", {"user_id": 1, "course_id": 1}),
        ("PATCH", "/api/edit-grants/1", {"user_id": 1}),
        ("DELETE", "/api/edit-grants/1", None),
    ],
)
async def test_edit_grant_routes_require_auth(client, method, path, json_body):
    """Edit-grant routes reject a missing session."""
    kwargs = {} if json_body is None else {"json": json_body}
    response = await client.request(method, path, **kwargs)
    assert_error(response, 401, "Not authenticated")


# GET /api/edit-grants


@pytest.mark.asyncio
async def test_list_edit_grants_scopes_by_role(
    client: AsyncClient,
    world,
    super_cookies,
    admin_cookies,
    other_admin_cookies,
    educator_cookies,
    student_cookies,
):
    """GET /api/edit-grants returns the rows each role is allowed to see."""
    student_response = await client.get("/api/edit-grants", cookies=student_cookies)
    assert student_response.status_code == 200, student_response.text
    assert student_response.json() == []

    educator_response = await client.get("/api/edit-grants", cookies=educator_cookies)
    assert educator_response.status_code == 200, educator_response.text
    rows = educator_response.json()
    assert len(rows) == 1
    assert_grant_shape(rows[0])
    assert rows[0]["id"] == world.edit_grant_id
    assert rows[0]["user_id"] == world.educator.id

    admin_response = await client.get("/api/edit-grants", cookies=admin_cookies)
    assert [row["id"] for row in admin_response.json()] == [world.edit_grant_id]

    other_admin_response = await client.get(
        "/api/edit-grants", cookies=other_admin_cookies
    )
    assert other_admin_response.json() == []

    super_response = await client.get("/api/edit-grants", cookies=super_cookies)
    assert [row["id"] for row in super_response.json()] == [world.edit_grant_id]


# POST /api/edit-grants


@pytest.mark.asyncio
async def test_grant_lets_educator_edit_until_it_is_removed(
    client: AsyncClient, world, admin_cookies, other_educator_cookies
):
    """An edit grant allows course edits, and deleting it removes that access."""
    denied = await client.patch(
        f"/api/courses/{world.course_id}",
        json={"name": "Before grant"},
        cookies=other_educator_cookies,
    )
    assert_error(denied, 403, "You cannot edit this course")

    created = await client.post(
        "/api/edit-grants",
        json={"user_id": world.other_educator.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert_grant_shape(body)
    assert body["user_id"] == world.other_educator.id

    allowed = await client.patch(
        f"/api/courses/{world.course_id}",
        json={"name": "After grant"},
        cookies=other_educator_cookies,
    )
    assert allowed.status_code == 200, allowed.text

    deleted = await client.delete(
        f"/api/edit-grants/{body['id']}", cookies=admin_cookies
    )
    assert deleted.status_code == 204, deleted.text
    removed = await client.patch(
        f"/api/courses/{world.course_id}",
        json={"name": "After delete"},
        cookies=other_educator_cookies,
    )
    assert_error(removed, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_create_edit_grant_duplicate(client: AsyncClient, world, admin_cookies):
    """POST /api/edit-grants rejects a grant that already exists."""
    response = await client.post(
        "/api/edit-grants",
        json={"user_id": world.educator.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert_error(response, 409, "Edit grant already exists")


@pytest.mark.asyncio
async def test_create_edit_grant_requires_educator(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/edit-grants rejects a student."""
    response = await client.post(
        "/api/edit-grants",
        json={"user_id": world.student.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert_error(response, 422, "Edit grant requires an educator")


@pytest.mark.asyncio
async def test_create_edit_grant_requires_same_group(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/edit-grants rejects an educator from another group."""
    response = await client.post(
        "/api/edit-grants",
        json={"user_id": world.outsider_educator.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert_error(response, 422, "Educator must belong to this course's group")


@pytest.mark.asyncio
async def test_create_edit_grant_unknown_course(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/edit-grants returns 404 when the course does not exist."""
    response = await client.post(
        "/api/edit-grants",
        json={"user_id": world.educator.id, "course_id": MISSING_ID},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Course not found")


@pytest.mark.asyncio
async def test_create_edit_grant_unknown_user(client: AsyncClient, world, admin_cookies):
    """POST /api/edit-grants returns 404 when the user does not exist."""
    response = await client.post(
        "/api/edit-grants",
        json={"user_id": MISSING_ID, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "User not found")


@pytest.mark.asyncio
async def test_create_edit_grant_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """POST /api/edit-grants rejects a student."""
    response = await client.post(
        "/api/edit-grants",
        json={"user_id": world.other_educator.id, "course_id": world.course_id},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_create_edit_grant_forbidden_without_grant(
    client: AsyncClient, world, other_educator_cookies
):
    """POST /api/edit-grants rejects an educator who cannot edit the course."""
    response = await client.post(
        "/api/edit-grants",
        json={"user_id": world.educator.id, "course_id": world.course_id},
        cookies=other_educator_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


# PATCH /api/edit-grants/{grant_id}


@pytest.mark.asyncio
async def test_update_edit_grant_moves_access(
    client: AsyncClient, world, admin_cookies, educator_cookies
):
    """PATCH /api/edit-grants/{id} moves edit access onto another course."""
    created = await client.post(
        "/api/courses",
        json={"name": "Second", "group_id": world.group_id},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text
    course_id = created.json()["id"]
    response = await client.patch(
        f"/api/edit-grants/{world.edit_grant_id}",
        json={"course_id": course_id},
        cookies=admin_cookies,
    )
    assert response.status_code == 200, response.text
    assert response.json()["course_id"] == course_id

    lost = await client.patch(
        f"/api/courses/{world.course_id}",
        json={"name": "Old"},
        cookies=educator_cookies,
    )
    assert_error(lost, 403, "You cannot edit this course")
    gained = await client.patch(
        f"/api/courses/{course_id}",
        json={"name": "New"},
        cookies=educator_cookies,
    )
    assert gained.status_code == 200, gained.text


@pytest.mark.asyncio
async def test_update_edit_grant_duplicate(client: AsyncClient, world, admin_cookies):
    """PATCH /api/edit-grants/{id} rejects a pair that already exists."""
    created = await client.post(
        "/api/edit-grants",
        json={"user_id": world.other_educator.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text
    response = await client.patch(
        f"/api/edit-grants/{created.json()['id']}",
        json={"user_id": world.educator.id},
        cookies=admin_cookies,
    )
    assert_error(response, 409, "Edit grant already exists")


@pytest.mark.asyncio
async def test_update_edit_grant_rejects_other_group(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/edit-grants/{id} rejects an educator from another group."""
    response = await client.patch(
        f"/api/edit-grants/{world.edit_grant_id}",
        json={"user_id": world.outsider_educator.id},
        cookies=admin_cookies,
    )
    assert_error(response, 422, "Educator must belong to this course's group")


@pytest.mark.asyncio
async def test_update_edit_grant_rejects_other_course(
    client: AsyncClient, world, admin_cookies, other_admin_cookies
):
    """PATCH /api/edit-grants/{id} rejects a course the editor cannot edit."""
    created = await client.post(
        "/api/courses",
        json={"name": "Foreign", "group_id": world.other_group_id},
        cookies=other_admin_cookies,
    )
    assert created.status_code == 201, created.text
    response = await client.patch(
        f"/api/edit-grants/{world.edit_grant_id}",
        json={"course_id": created.json()["id"]},
        cookies=admin_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_update_edit_grant_requires_a_change(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/edit-grants/{id} rejects an empty body."""
    response = await client.patch(
        f"/api/edit-grants/{world.edit_grant_id}", json={}, cookies=admin_cookies
    )
    assert response.status_code == 422, response.text
    assert "user_id or course_id is required" in response.text


@pytest.mark.asyncio
async def test_update_edit_grant_not_found(client: AsyncClient, admin_cookies):
    """PATCH /api/edit-grants/{id} returns 404 for a missing grant."""
    response = await client.patch(
        f"/api/edit-grants/{MISSING_ID}",
        json={"user_id": 1},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Edit grant not found")


@pytest.mark.asyncio
async def test_update_edit_grant_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """PATCH /api/edit-grants/{id} rejects a student."""
    response = await client.patch(
        f"/api/edit-grants/{world.edit_grant_id}",
        json={"user_id": world.other_educator.id},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


# DELETE /api/edit-grants/{grant_id}


@pytest.mark.asyncio
async def test_delete_edit_grant_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """DELETE /api/edit-grants/{id} rejects a student."""
    response = await client.delete(
        f"/api/edit-grants/{world.edit_grant_id}", cookies=student_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_delete_edit_grant_not_found(client: AsyncClient, admin_cookies):
    """DELETE /api/edit-grants/{id} returns 404 for a missing grant."""
    response = await client.delete(
        f"/api/edit-grants/{MISSING_ID}", cookies=admin_cookies
    )
    assert_error(response, 404, "Edit grant not found")
