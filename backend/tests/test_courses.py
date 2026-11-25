"""
Contract-level tests for the /api/courses endpoints
"""

import pytest
from httpx import AsyncClient

from tests.helpers import MISSING_ID, assert_course_shape, assert_error


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/courses", None),
        ("GET", "/api/courses/1", None),
        ("POST", "/api/courses", {"name": "Nope", "group_id": 1}),
        ("PATCH", "/api/courses/1", {"name": "Nope"}),
        ("DELETE", "/api/courses/1", None),
    ],
)
async def test_course_routes_require_auth(client, method, path, json_body):
    """Course routes reject a missing session."""
    kwargs = {} if json_body is None else {"json": json_body}
    response = await client.request(method, path, **kwargs)
    assert_error(response, 401, "Not authenticated")


# GET /api/courses


@pytest.mark.asyncio
async def test_list_courses_scopes_by_role(
    client: AsyncClient,
    world,
    super_cookies,
    admin_cookies,
    other_admin_cookies,
    educator_cookies,
    student_cookies,
):
    """GET /api/courses returns courses visible to each role."""
    other = await client.post(
        "/api/courses",
        json={"name": "Other course", "group_id": world.other_group_id},
        cookies=other_admin_cookies,
    )
    assert other.status_code == 201, other.text
    other_id = other.json()["id"]

    super_response = await client.get("/api/courses", cookies=super_cookies)
    assert super_response.status_code == 200, super_response.text
    super_ids = [course["id"] for course in super_response.json()]
    assert sorted(super_ids) == sorted({world.course_id, other_id})
    for course in super_response.json():
        assert_course_shape(course)

    admin_response = await client.get("/api/courses", cookies=admin_cookies)
    assert [course["id"] for course in admin_response.json()] == [world.course_id]

    educator_response = await client.get("/api/courses", cookies=educator_cookies)
    assert [course["id"] for course in educator_response.json()] == [world.course_id]

    student_response = await client.get("/api/courses", cookies=student_cookies)
    assert [course["id"] for course in student_response.json()] == [world.course_id]

    hidden = await client.get("/api/courses", cookies=other_admin_cookies)
    assert [course["id"] for course in hidden.json()] == [other_id]


@pytest.mark.asyncio
async def test_list_courses_for_one_group(client: AsyncClient, world, educator_cookies):
    """GET /api/courses?group_id limits the list to that group."""
    response = await client.get(
        "/api/courses",
        params={"group_id": world.group_id},
        cookies=educator_cookies,
    )
    assert response.status_code == 200, response.text
    assert [course["group_id"] for course in response.json()] == [world.group_id]


@pytest.mark.asyncio
async def test_student_list_hides_unenrolled_course(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """A student list omits courses in their group that they are not enrolled in."""
    created = await client.post(
        "/api/courses",
        json={"name": "Unenrolled", "group_id": world.group_id},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text
    response = await client.get("/api/courses", cookies=student_cookies)
    assert [course["id"] for course in response.json()] == [world.course_id]


@pytest.mark.asyncio
async def test_list_courses_unknown_group(client: AsyncClient, admin_cookies):
    """GET /api/courses?group_id returns 404 when the group does not exist."""
    response = await client.get(
        "/api/courses", params={"group_id": MISSING_ID}, cookies=admin_cookies
    )
    assert_error(response, 404, "Group not found")


@pytest.mark.asyncio
async def test_list_courses_forbidden_group(
    client: AsyncClient, world, educator_cookies
):
    """GET /api/courses?group_id rejects a group the caller cannot view."""
    response = await client.get(
        "/api/courses",
        params={"group_id": world.other_group_id},
        cookies=educator_cookies,
    )
    assert_error(response, 403, "You cannot view this group")


@pytest.mark.asyncio
async def test_list_courses_rejects_bad_group_id(client: AsyncClient, admin_cookies):
    """GET /api/courses rejects a non-integer group_id."""
    response = await client.get(
        "/api/courses", params={"group_id": "abc"}, cookies=admin_cookies
    )
    assert response.status_code == 422, response.text


# GET /api/courses/{course_id}


@pytest.mark.asyncio
async def test_get_course(client: AsyncClient, world, student_cookies):
    """GET /api/courses/{id} returns a course the student is enrolled in."""
    response = await client.get(
        f"/api/courses/{world.course_id}", cookies=student_cookies
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert_course_shape(body)
    assert body["id"] == world.course_id
    assert body["group_id"] == world.group_id
    assert body["created_by"] == world.admin.id


@pytest.mark.asyncio
async def test_get_course_forbidden_for_unenrolled_student(
    client: AsyncClient, world, other_student_cookies
):
    """GET /api/courses/{id} rejects a student who is not enrolled."""
    response = await client.get(
        f"/api/courses/{world.course_id}", cookies=other_student_cookies
    )
    assert_error(response, 403, "You cannot view this course")


@pytest.mark.asyncio
async def test_get_course_not_found(client: AsyncClient, admin_cookies):
    """GET /api/courses/{id} returns 404 for a missing course."""
    response = await client.get(f"/api/courses/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Course not found")


@pytest.mark.asyncio
async def test_get_course_rejects_string_id(client: AsyncClient, admin_cookies):
    """GET /api/courses/{id} rejects a non-integer id."""
    response = await client.get("/api/courses/nope", cookies=admin_cookies)
    assert response.status_code == 422, response.text


# POST /api/courses


@pytest.mark.asyncio
async def test_admin_creates_course_in_own_group(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/courses lets an admin create a course in a group they created."""
    response = await client.post(
        "/api/courses",
        json={"name": "  Admin course  ", "group_id": world.group_id},
        cookies=admin_cookies,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert_course_shape(body)
    assert body["name"] == "Admin course"
    assert body["created_by"] == world.admin.id
    assert body["group_id"] == world.group_id


@pytest.mark.asyncio
async def test_educator_create_adds_edit_grant(
    client: AsyncClient, world, educator_cookies
):
    """POST /api/courses grants the creating educator edit access."""
    response = await client.post(
        "/api/courses",
        json={"name": "Educator course", "group_id": world.group_id},
        cookies=educator_cookies,
    )
    assert response.status_code == 201, response.text
    course_id = response.json()["id"]
    grants = await client.get("/api/edit-grants", cookies=educator_cookies)
    assert grants.status_code == 200, grants.text
    assert any(
        grant["course_id"] == course_id and grant["user_id"] == world.educator.id
        for grant in grants.json()
    )
    renamed = await client.patch(
        f"/api/courses/{course_id}",
        json={"name": "Renamed by educator"},
        cookies=educator_cookies,
    )
    assert renamed.status_code == 200, renamed.text


@pytest.mark.asyncio
async def test_super_user_create_does_not_add_edit_grant(
    client: AsyncClient, world, super_cookies
):
    """POST /api/courses does not add an edit grant for a super-user."""
    response = await client.post(
        "/api/courses",
        json={"name": "Super course", "group_id": world.other_group_id},
        cookies=super_cookies,
    )
    assert response.status_code == 201, response.text
    course_id = response.json()["id"]
    grants = await client.get("/api/edit-grants", cookies=super_cookies)
    assert all(grant["course_id"] != course_id for grant in grants.json())


@pytest.mark.asyncio
async def test_create_course_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """POST /api/courses rejects a student."""
    response = await client.post(
        "/api/courses",
        json={"name": "Nope", "group_id": world.group_id},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot create courses")


@pytest.mark.asyncio
async def test_educator_cannot_create_course_in_another_group(
    client: AsyncClient, world, educator_cookies
):
    """POST /api/courses rejects an educator creating outside their group."""
    response = await client.post(
        "/api/courses",
        json={"name": "Nope", "group_id": world.other_group_id},
        cookies=educator_cookies,
    )
    assert_error(response, 403, "You cannot create a course in this group")


@pytest.mark.asyncio
async def test_admin_cannot_create_course_in_another_admins_group(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/courses rejects an admin creating in a group they do not own."""
    response = await client.post(
        "/api/courses",
        json={"name": "Nope", "group_id": world.other_group_id},
        cookies=admin_cookies,
    )
    assert_error(response, 403, "You cannot create a course in this group")


@pytest.mark.asyncio
async def test_create_course_unknown_group(client: AsyncClient, super_cookies):
    """POST /api/courses returns 404 when the group does not exist."""
    response = await client.post(
        "/api/courses",
        json={"name": "Nope", "group_id": MISSING_ID},
        cookies=super_cookies,
    )
    assert_error(response, 404, "Group not found")


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["", "   "])
async def test_create_course_rejects_blank_name(
    client: AsyncClient, world, admin_cookies, name
):
    """POST /api/courses rejects a blank name."""
    response = await client.post(
        "/api/courses",
        json={"name": name, "group_id": world.group_id},
        cookies=admin_cookies,
    )
    assert response.status_code == 422, response.text


# PATCH /api/courses/{course_id}


@pytest.mark.asyncio
async def test_update_course(client: AsyncClient, world, educator_cookies):
    """PATCH /api/courses/{id} lets an educator with a grant rename the course."""
    response = await client.patch(
        f"/api/courses/{world.course_id}",
        json={"name": "  Renamed course  "},
        cookies=educator_cookies,
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Renamed course"


@pytest.mark.asyncio
async def test_update_course_forbidden_without_grant(
    client: AsyncClient, world, other_educator_cookies
):
    """PATCH /api/courses/{id} rejects an educator who has no edit grant."""
    response = await client.patch(
        f"/api/courses/{world.course_id}",
        json={"name": "Stolen"},
        cookies=other_educator_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_update_course_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """PATCH /api/courses/{id} rejects a student."""
    response = await client.patch(
        f"/api/courses/{world.course_id}",
        json={"name": "Stolen"},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_update_course_not_found(client: AsyncClient, admin_cookies):
    """PATCH /api/courses/{id} returns 404 for a missing course."""
    response = await client.patch(
        f"/api/courses/{MISSING_ID}", json={"name": "Nope"}, cookies=admin_cookies
    )
    assert_error(response, 404, "Course not found")


@pytest.mark.asyncio
async def test_update_course_rejects_blank_name(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/courses/{id} rejects a blank name."""
    response = await client.patch(
        f"/api/courses/{world.course_id}",
        json={"name": "   "},
        cookies=admin_cookies,
    )
    assert response.status_code == 422, response.text


# DELETE /api/courses/{course_id}


@pytest.mark.asyncio
async def test_delete_course_removes_enrollments_and_grants(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """DELETE /api/courses/{id} drops enrollments and grants, then the course."""
    created = await client.post(
        "/api/courses",
        json={"name": "Disposable", "group_id": world.group_id},
        cookies=admin_cookies,
    )
    assert created.status_code == 201, created.text
    course_id = created.json()["id"]
    enrolled = await client.post(
        "/api/enrollments",
        json={"user_id": world.student.id, "course_id": course_id},
        cookies=admin_cookies,
    )
    assert enrolled.status_code == 201, enrolled.text
    enrollment_id = enrolled.json()["id"]

    response = await client.delete(f"/api/courses/{course_id}", cookies=admin_cookies)
    assert response.status_code == 204, response.text
    follow = await client.get(f"/api/courses/{course_id}", cookies=admin_cookies)
    assert_error(follow, 404, "Course not found")
    listing = await client.get("/api/enrollments", cookies=student_cookies)
    assert enrollment_id not in {row["id"] for row in listing.json()}


@pytest.mark.asyncio
async def test_delete_course_with_module_conflicts_and_rolls_back(
    client: AsyncClient, world, admin_cookies, student_cookies, educator_cookies
):
    """DELETE /api/courses/{id} returns 409 when a module remains, and keeps access."""
    response = await client.delete(
        f"/api/courses/{world.course_id}", cookies=admin_cookies
    )
    assert_error(response, 409, "Course is still referenced by another record")
    still_visible = await client.get(
        f"/api/courses/{world.course_id}", cookies=student_cookies
    )
    assert still_visible.status_code == 200, still_visible.text
    still_editable = await client.patch(
        f"/api/courses/{world.course_id}",
        json={"name": "Still editable"},
        cookies=educator_cookies,
    )
    assert still_editable.status_code == 200, still_editable.text


@pytest.mark.asyncio
async def test_delete_course_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """DELETE /api/courses/{id} rejects a student."""
    response = await client.delete(
        f"/api/courses/{world.course_id}", cookies=student_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_delete_course_not_found(client: AsyncClient, admin_cookies):
    """DELETE /api/courses/{id} returns 404 for a missing course."""
    response = await client.delete(f"/api/courses/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Course not found")
