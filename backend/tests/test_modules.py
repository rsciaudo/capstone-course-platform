"""
Contract-level tests for the /api/modules endpoints
"""

import pytest
from httpx import AsyncClient

from tests.helpers import (
    MISSING_ID,
    assert_error,
    assert_module_shape,
    upload_parts,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/modules", None),
        ("GET", "/api/modules/1", None),
        ("POST", "/api/modules", {"name": "Nope", "course_id": 1, "position": 1}),
        ("PATCH", "/api/modules/1", {"name": "Nope"}),
        ("DELETE", "/api/modules/1", None),
    ],
)
async def test_module_routes_require_auth(client, method, path, json_body):
    """Module routes reject a missing session."""
    kwargs = {} if json_body is None else {"json": json_body}
    response = await client.request(method, path, **kwargs)
    assert_error(response, 401, "Not authenticated")


# GET /api/modules


@pytest.mark.asyncio
async def test_list_modules_scopes_by_role(
    client: AsyncClient,
    world,
    super_cookies,
    admin_cookies,
    other_admin_cookies,
    educator_cookies,
    student_cookies,
):
    """GET /api/modules returns modules from courses the caller can view."""
    other_course = await client.post(
        "/api/courses",
        json={"name": "Other course", "group_id": world.other_group_id},
        cookies=other_admin_cookies,
    )
    assert other_course.status_code == 201, other_course.text
    other_module = await client.post(
        "/api/modules",
        json={
            "name": "Other module",
            "course_id": other_course.json()["id"],
            "position": 1,
        },
        cookies=other_admin_cookies,
    )
    assert other_module.status_code == 201, other_module.text
    other_id = other_module.json()["id"]

    super_response = await client.get("/api/modules", cookies=super_cookies)
    assert super_response.status_code == 200, super_response.text
    super_ids = [module["id"] for module in super_response.json()]
    assert sorted(super_ids) == sorted({world.module_id, other_id})
    for module in super_response.json():
        assert_module_shape(module)

    for cookies in (admin_cookies, educator_cookies, student_cookies):
        response = await client.get("/api/modules", cookies=cookies)
        assert [module["id"] for module in response.json()] == [world.module_id]

    hidden = await client.get("/api/modules", cookies=other_admin_cookies)
    assert [module["id"] for module in hidden.json()] == [other_id]


@pytest.mark.asyncio
async def test_student_list_hides_unenrolled_course(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """A student list omits modules from courses they are not enrolled in."""
    created = await client.post(
        "/api/courses",
        json={"name": "Unenrolled", "group_id": world.group_id},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text
    module = await client.post(
        "/api/modules",
        json={"name": "Hidden", "course_id": created.json()["id"], "position": 1},
        cookies=admin_cookies,
    )
    assert module.status_code == 201, module.text
    response = await client.get("/api/modules", cookies=student_cookies)
    assert [row["id"] for row in response.json()] == [world.module_id]


@pytest.mark.asyncio
async def test_list_modules_for_one_course(client: AsyncClient, world, student_cookies):
    """GET /api/modules?course_id returns that course when the caller can view it."""
    response = await client.get(
        "/api/modules",
        params={"course_id": world.course_id},
        cookies=student_cookies,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert [module["id"] for module in body] == [world.module_id]
    assert body[0]["position"] == 1


@pytest.mark.asyncio
async def test_list_modules_forbidden_course(
    client: AsyncClient, world, other_student_cookies
):
    """GET /api/modules?course_id rejects a course the caller cannot view."""
    response = await client.get(
        "/api/modules",
        params={"course_id": world.course_id},
        cookies=other_student_cookies,
    )
    assert_error(response, 403, "You cannot view this course")


@pytest.mark.asyncio
async def test_list_modules_unknown_course(client: AsyncClient, admin_cookies):
    """GET /api/modules?course_id returns 404 when the course does not exist."""
    response = await client.get(
        "/api/modules", params={"course_id": MISSING_ID}, cookies=admin_cookies
    )
    assert_error(response, 404, "Course not found")


@pytest.mark.asyncio
async def test_list_modules_rejects_bad_course_id(client: AsyncClient, admin_cookies):
    """GET /api/modules rejects a non-integer course_id."""
    response = await client.get(
        "/api/modules", params={"course_id": "abc"}, cookies=admin_cookies
    )
    assert response.status_code == 422, response.text


# GET /api/modules/{module_id}


@pytest.mark.asyncio
async def test_get_module(client: AsyncClient, world, student_cookies):
    """GET /api/modules/{id} returns a module in an enrolled course."""
    response = await client.get(
        f"/api/modules/{world.module_id}", cookies=student_cookies
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert_module_shape(body)
    assert body["id"] == world.module_id
    assert body["course_id"] == world.course_id
    assert body["name"] == "Demo module"


@pytest.mark.asyncio
async def test_get_module_forbidden(client: AsyncClient, world, other_student_cookies):
    """GET /api/modules/{id} rejects a student who is not enrolled."""
    response = await client.get(
        f"/api/modules/{world.module_id}", cookies=other_student_cookies
    )
    assert_error(response, 403, "You cannot view this course")


@pytest.mark.asyncio
async def test_get_module_not_found(client: AsyncClient, admin_cookies):
    """GET /api/modules/{id} returns 404 for a missing module."""
    response = await client.get(f"/api/modules/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Module not found")


@pytest.mark.asyncio
async def test_get_module_rejects_string_id(client: AsyncClient, admin_cookies):
    """GET /api/modules/{id} rejects a non-integer id."""
    response = await client.get("/api/modules/nope", cookies=admin_cookies)
    assert response.status_code == 422, response.text


# POST /api/modules


@pytest.mark.asyncio
async def test_create_module(client: AsyncClient, world, educator_cookies):
    """POST /api/modules lets an educator with a grant add a module."""
    response = await client.post(
        "/api/modules",
        json={
            "name": "  Week two  ",
            "course_id": world.course_id,
            "position": 2,
        },
        cookies=educator_cookies,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert_module_shape(body)
    assert body["name"] == "Week two"
    assert body["position"] == 2
    assert body["course_id"] == world.course_id


@pytest.mark.asyncio
async def test_create_module_duplicate_position(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/modules rejects a position that is already used."""
    response = await client.post(
        "/api/modules",
        json={"name": "Clash", "course_id": world.course_id, "position": 1},
        cookies=admin_cookies,
    )
    assert_error(response, 409, "A module with this position already exists")


@pytest.mark.asyncio
async def test_create_module_unknown_course(client: AsyncClient, admin_cookies):
    """POST /api/modules returns 404 when the course does not exist."""
    response = await client.post(
        "/api/modules",
        json={"name": "Nope", "course_id": MISSING_ID, "position": 1},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Course not found")


@pytest.mark.asyncio
async def test_create_module_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """POST /api/modules rejects a student."""
    response = await client.post(
        "/api/modules",
        json={"name": "Nope", "course_id": world.course_id, "position": 2},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_create_module_forbidden_without_grant(
    client: AsyncClient, world, other_educator_cookies
):
    """POST /api/modules rejects an educator who has no edit grant."""
    response = await client.post(
        "/api/modules",
        json={"name": "Nope", "course_id": world.course_id, "position": 2},
        cookies=other_educator_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"name": "   ", "position": 2},
        {"name": "Zero", "position": 0},
        {"name": "Bad course", "course_id": "abc", "position": 2},
    ],
)
async def test_create_module_rejects_invalid_body(
    client: AsyncClient, world, admin_cookies, payload
):
    """POST /api/modules rejects a blank name, a non-positive position, and a bad id."""
    body = {"course_id": world.course_id, "position": 2, **payload}
    response = await client.post("/api/modules", json=body, cookies=admin_cookies)
    assert response.status_code == 422, response.text


# PATCH /api/modules/{module_id}


@pytest.mark.asyncio
async def test_update_module(client: AsyncClient, world, educator_cookies):
    """PATCH /api/modules/{id} renames a module and can move its position."""
    response = await client.patch(
        f"/api/modules/{world.module_id}",
        json={"name": "  Renamed module  ", "position": 3},
        cookies=educator_cookies,
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Renamed module"
    assert response.json()["position"] == 3


@pytest.mark.asyncio
async def test_update_module_duplicate_position(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/modules/{id} rejects a position another module already uses."""
    created = await client.post(
        "/api/modules",
        json={"name": "Second", "course_id": world.course_id, "position": 2},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text
    response = await client.patch(
        f"/api/modules/{created.json()['id']}",
        json={"position": 1},
        cookies=admin_cookies,
    )
    assert_error(response, 409, "A module with this position already exists")


@pytest.mark.asyncio
async def test_update_module_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """PATCH /api/modules/{id} rejects a student."""
    response = await client.patch(
        f"/api/modules/{world.module_id}",
        json={"name": "Stolen"},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_update_module_not_found(client: AsyncClient, admin_cookies):
    """PATCH /api/modules/{id} returns 404 for a missing module."""
    response = await client.patch(
        f"/api/modules/{MISSING_ID}", json={"name": "Nope"}, cookies=admin_cookies
    )
    assert_error(response, 404, "Module not found")


@pytest.mark.asyncio
async def test_update_module_rejects_blank_name(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/modules/{id} rejects a blank name."""
    response = await client.patch(
        f"/api/modules/{world.module_id}",
        json={"name": "   "},
        cookies=admin_cookies,
    )
    assert response.status_code == 422, response.text


# DELETE /api/modules/{module_id}


@pytest.mark.asyncio
async def test_delete_module_removes_stored_files(
    client: AsyncClient, world, admin_cookies, tmp_path
):
    """DELETE /api/modules/{id} removes the module and files stored for its content."""
    uploaded = await client.post(
        "/api/files",
        cookies=admin_cookies,
        **upload_parts(world.module_id),
    )
    assert uploaded.status_code == 201, uploaded.text
    assert list(tmp_path.iterdir())
    response = await client.delete(
        f"/api/modules/{world.module_id}", cookies=admin_cookies
    )
    assert response.status_code == 204, response.text
    assert list(tmp_path.iterdir()) == []
    follow = await client.get(f"/api/modules/{world.module_id}", cookies=admin_cookies)
    assert_error(follow, 404, "Module not found")


@pytest.mark.asyncio
async def test_delete_module_forbidden_for_student(
    client: AsyncClient, world, student_cookies, admin_cookies, tmp_path
):
    """DELETE /api/modules/{id} rejects a student and leaves stored files in place."""
    uploaded = await client.post(
        "/api/files",
        cookies=admin_cookies,
        **upload_parts(world.module_id),
    )
    assert uploaded.status_code == 201, uploaded.text
    before = list(tmp_path.iterdir())
    response = await client.delete(
        f"/api/modules/{world.module_id}", cookies=student_cookies
    )
    assert_error(response, 403, "You cannot edit this course")
    assert list(tmp_path.iterdir()) == before


@pytest.mark.asyncio
async def test_delete_module_not_found(client: AsyncClient, admin_cookies):
    """DELETE /api/modules/{id} returns 404 for a missing module."""
    response = await client.delete(f"/api/modules/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Module not found")
