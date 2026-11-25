"""
Contract-level tests for the /api/enrollments endpoints
"""

import pytest
from httpx import AsyncClient

from tests.helpers import MISSING_ID, assert_enrollment_shape, assert_error


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/enrollments", None),
        ("POST", "/api/enrollments", {"user_id": 1, "course_id": 1}),
        ("PATCH", "/api/enrollments/1", {"user_id": 1}),
        ("DELETE", "/api/enrollments/1", None),
    ],
)
async def test_enrollment_routes_require_auth(client, method, path, json_body):
    """Enrollment routes reject a missing session."""
    kwargs = {} if json_body is None else {"json": json_body}
    response = await client.request(method, path, **kwargs)
    assert_error(response, 401, "Not authenticated")


# GET /api/enrollments


@pytest.mark.asyncio
async def test_list_enrollments_scopes_by_role(
    client: AsyncClient,
    world,
    super_cookies,
    admin_cookies,
    other_admin_cookies,
    educator_cookies,
    student_cookies,
):
    """GET /api/enrollments returns the rows each role is allowed to see."""
    created = await client.post(
        "/api/enrollments",
        json={"user_id": world.other_student.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text

    student_response = await client.get("/api/enrollments", cookies=student_cookies)
    assert student_response.status_code == 200, student_response.text
    student_rows = student_response.json()
    assert [row["user_id"] for row in student_rows] == [world.student.id]
    assert_enrollment_shape(student_rows[0])

    educator_response = await client.get("/api/enrollments", cookies=educator_cookies)
    assert {row["user_id"] for row in educator_response.json()} == {
        world.student.id,
        world.other_student.id,
    }

    admin_response = await client.get("/api/enrollments", cookies=admin_cookies)
    assert {row["id"] for row in admin_response.json()} == {
        row["id"] for row in educator_response.json()
    }

    other_admin_response = await client.get(
        "/api/enrollments", cookies=other_admin_cookies
    )
    assert other_admin_response.json() == []

    super_response = await client.get("/api/enrollments", cookies=super_cookies)
    assert {row["user_id"] for row in super_response.json()} == {
        world.student.id,
        world.other_student.id,
    }


# POST /api/enrollments


@pytest.mark.asyncio
async def test_create_enrollment(client: AsyncClient, world, admin_cookies):
    """POST /api/enrollments enrolls a student from the course group."""
    response = await client.post(
        "/api/enrollments",
        json={"user_id": world.other_student.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert_enrollment_shape(body)
    assert body["user_id"] == world.other_student.id
    assert body["course_id"] == world.course_id


@pytest.mark.asyncio
async def test_create_enrollment_duplicate(client: AsyncClient, world, admin_cookies):
    """POST /api/enrollments rejects a student who is already enrolled."""
    response = await client.post(
        "/api/enrollments",
        json={"user_id": world.student.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert_error(response, 409, "Enrollment already exists")


@pytest.mark.asyncio
async def test_create_enrollment_requires_student(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/enrollments rejects an educator."""
    response = await client.post(
        "/api/enrollments",
        json={"user_id": world.educator.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert_error(response, 422, "Enrollment requires a student")


@pytest.mark.asyncio
async def test_create_enrollment_requires_same_group(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/enrollments rejects a student from another group."""
    response = await client.post(
        "/api/enrollments",
        json={"user_id": world.outsider_student.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert_error(response, 422, "Student must belong to this course's group")


@pytest.mark.asyncio
async def test_create_enrollment_unknown_course(client: AsyncClient, world, admin_cookies):
    """POST /api/enrollments returns 404 when the course does not exist."""
    response = await client.post(
        "/api/enrollments",
        json={"user_id": world.student.id, "course_id": MISSING_ID},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Course not found")


@pytest.mark.asyncio
async def test_create_enrollment_unknown_user(client: AsyncClient, world, admin_cookies):
    """POST /api/enrollments returns 404 when the user does not exist."""
    response = await client.post(
        "/api/enrollments",
        json={"user_id": MISSING_ID, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "User not found")


@pytest.mark.asyncio
async def test_create_enrollment_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """POST /api/enrollments rejects a student."""
    response = await client.post(
        "/api/enrollments",
        json={"user_id": world.other_student.id, "course_id": world.course_id},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_create_enrollment_forbidden_without_grant(
    client: AsyncClient, world, other_educator_cookies
):
    """POST /api/enrollments rejects an educator who cannot edit the course."""
    response = await client.post(
        "/api/enrollments",
        json={"user_id": world.other_student.id, "course_id": world.course_id},
        cookies=other_educator_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


# PATCH /api/enrollments/{enrollment_id}


@pytest.mark.asyncio
async def test_update_enrollment_moves_student_to_another_course(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """PATCH /api/enrollments/{id} can point the enrollment at another course."""
    created = await client.post(
        "/api/courses",
        json={"name": "Second", "group_id": world.group_id},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text
    course_id = created.json()["id"]
    response = await client.patch(
        f"/api/enrollments/{world.enrollment_id}",
        json={"course_id": course_id},
        cookies=admin_cookies,
    )
    assert response.status_code == 200, response.text
    assert response.json()["course_id"] == course_id
    visible = await client.get(f"/api/courses/{course_id}", cookies=student_cookies)
    assert visible.status_code == 200, visible.text
    hidden = await client.get(
        f"/api/courses/{world.course_id}", cookies=student_cookies
    )
    assert_error(hidden, 403, "You cannot view this course")


@pytest.mark.asyncio
async def test_update_enrollment_duplicate(client: AsyncClient, world, admin_cookies):
    """PATCH /api/enrollments/{id} rejects a pair that already exists."""
    created = await client.post(
        "/api/enrollments",
        json={"user_id": world.other_student.id, "course_id": world.course_id},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text
    response = await client.patch(
        f"/api/enrollments/{created.json()['id']}",
        json={"user_id": world.student.id},
        cookies=admin_cookies,
    )
    assert_error(response, 409, "Enrollment already exists")


@pytest.mark.asyncio
async def test_update_enrollment_rejects_other_group_course(
    client: AsyncClient, world, admin_cookies, other_admin_cookies
):
    """PATCH /api/enrollments/{id} rejects a course the editor cannot edit."""
    created = await client.post(
        "/api/courses",
        json={"name": "Foreign", "group_id": world.other_group_id},
        cookies=other_admin_cookies,
    )
    assert created.status_code == 201, created.text
    response = await client.patch(
        f"/api/enrollments/{world.enrollment_id}",
        json={"course_id": created.json()["id"]},
        cookies=admin_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_update_enrollment_requires_student(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/enrollments/{id} rejects moving the row onto an educator."""
    response = await client.patch(
        f"/api/enrollments/{world.enrollment_id}",
        json={"user_id": world.educator.id},
        cookies=admin_cookies,
    )
    assert_error(response, 422, "Enrollment requires a student")


@pytest.mark.asyncio
async def test_update_enrollment_requires_a_change(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/enrollments/{id} rejects an empty body."""
    response = await client.patch(
        f"/api/enrollments/{world.enrollment_id}", json={}, cookies=admin_cookies
    )
    assert response.status_code == 422, response.text
    assert "user_id or course_id is required" in response.text


@pytest.mark.asyncio
async def test_update_enrollment_rejects_null(client: AsyncClient, world, admin_cookies):
    """PATCH /api/enrollments/{id} rejects an explicit null."""
    response = await client.patch(
        f"/api/enrollments/{world.enrollment_id}",
        json={"user_id": None},
        cookies=admin_cookies,
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_update_enrollment_not_found(client: AsyncClient, admin_cookies):
    """PATCH /api/enrollments/{id} returns 404 for a missing enrollment."""
    response = await client.patch(
        f"/api/enrollments/{MISSING_ID}",
        json={"user_id": 1},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Enrollment not found")


@pytest.mark.asyncio
async def test_update_enrollment_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """PATCH /api/enrollments/{id} rejects a student."""
    response = await client.patch(
        f"/api/enrollments/{world.enrollment_id}",
        json={"user_id": world.other_student.id},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


# DELETE /api/enrollments/{enrollment_id}


@pytest.mark.asyncio
async def test_delete_enrollment(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """DELETE /api/enrollments/{id} removes the row and the student's access."""
    response = await client.delete(
        f"/api/enrollments/{world.enrollment_id}", cookies=admin_cookies
    )
    assert response.status_code == 204, response.text
    follow = await client.get(
        f"/api/courses/{world.course_id}", cookies=student_cookies
    )
    assert_error(follow, 403, "You cannot view this course")


@pytest.mark.asyncio
async def test_delete_enrollment_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """DELETE /api/enrollments/{id} rejects a student."""
    response = await client.delete(
        f"/api/enrollments/{world.enrollment_id}", cookies=student_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_delete_enrollment_not_found(client: AsyncClient, admin_cookies):
    """DELETE /api/enrollments/{id} returns 404 for a missing enrollment."""
    response = await client.delete(
        f"/api/enrollments/{MISSING_ID}", cookies=admin_cookies
    )
    assert_error(response, 404, "Enrollment not found")
