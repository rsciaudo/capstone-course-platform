"""
Contract-level tests for the /api/content endpoints
"""

import pytest
from httpx import AsyncClient

from tests.helpers import (
    MISSING_ID,
    assert_content_shape,
    assert_error,
    upload_parts,
)


def _slide(module_id: int, position: int, title: str = "Intro") -> dict:
    return {
        "module_id": module_id,
        "title": title,
        "position": position,
        "slide_data": "deck",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/content", None),
        ("GET", "/api/content/1", None),
        ("PATCH", "/api/content/1", {"title": "Nope"}),
        ("DELETE", "/api/content/1", None),
    ],
)
async def test_content_routes_require_auth(client, method, path, json_body):
    """Content routes reject a missing session."""
    kwargs = {} if json_body is None else {"json": json_body}
    response = await client.request(method, path, **kwargs)
    assert_error(response, 401, "Not authenticated")


# GET /api/content


@pytest.mark.asyncio
async def test_list_content_returns_each_type(
    client: AsyncClient, world, educator_cookies, student_cookies
):
    """GET /api/content returns file, slide, and quiz rows with their shapes."""
    slide = await client.post(
        "/api/slides", json=_slide(world.module_id, 1), cookies=educator_cookies
    )
    quiz = await client.post(
        "/api/quizzes",
        json={"module_id": world.module_id, "title": "Check", "position": 2},
        cookies=educator_cookies,
    )
    uploaded = await client.post(
        "/api/files",
        cookies=educator_cookies,
        **upload_parts(world.module_id, title="Notes", position=3),
    )
    assert slide.status_code == 201, slide.text
    assert quiz.status_code == 201, quiz.text
    assert uploaded.status_code == 201, uploaded.text

    response = await client.get(
        "/api/content", params={"module_id": world.module_id}, cookies=student_cookies
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert [item["type"] for item in body] == ["slide", "quiz", "file"]
    assert [item["position"] for item in body] == [1, 2, 3]
    for item in body:
        assert_content_shape(item)
    assert body[1]["questions"] == []
    assert body[2]["filename"] == "notes.pdf"


@pytest.mark.asyncio
async def test_list_content_scopes_by_role(
    client: AsyncClient,
    world,
    super_cookies,
    educator_cookies,
    student_cookies,
    other_student_cookies,
    other_admin_cookies,
):
    """GET /api/content hides items from courses the caller cannot view."""
    own = await client.post(
        "/api/slides", json=_slide(world.module_id, 1), cookies=educator_cookies
    )
    assert own.status_code == 201, own.text
    other_course = await client.post(
        "/api/courses",
        json={"name": "Other", "group_id": world.other_group_id},
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
    other = await client.post(
        "/api/slides",
        json=_slide(other_module.json()["id"], 1, "Foreign"),
        cookies=other_admin_cookies,
    )
    assert other.status_code == 201, other.text
    own_id = own.json()["id"]
    other_id = other.json()["id"]

    visible = await client.get("/api/content", cookies=student_cookies)
    assert [item["id"] for item in visible.json()] == [own_id]
    educator = await client.get("/api/content", cookies=educator_cookies)
    assert [item["id"] for item in educator.json()] == [own_id]
    super_response = await client.get("/api/content", cookies=super_cookies)
    assert sorted(item["id"] for item in super_response.json()) == sorted(
        {own_id, other_id}
    )
    hidden = await client.get(
        "/api/content",
        params={"module_id": world.module_id},
        cookies=other_student_cookies,
    )
    assert_error(hidden, 403, "You cannot view this course")


@pytest.mark.asyncio
async def test_list_content_orders_by_position(
    client: AsyncClient, world, admin_cookies
):
    """GET /api/content?module_id returns items in position order."""
    second = await client.post(
        "/api/slides", json=_slide(world.module_id, 2, "Second"), cookies=admin_cookies
    )
    first = await client.post(
        "/api/slides", json=_slide(world.module_id, 1, "First"), cookies=admin_cookies
    )
    assert second.status_code == 201, second.text
    assert first.status_code == 201, first.text
    response = await client.get(
        "/api/content", params={"module_id": world.module_id}, cookies=admin_cookies
    )
    assert [item["title"] for item in response.json()] == ["First", "Second"]


@pytest.mark.asyncio
async def test_list_content_unknown_module(client: AsyncClient, admin_cookies):
    """GET /api/content?module_id returns 404 when the module does not exist."""
    response = await client.get(
        "/api/content", params={"module_id": MISSING_ID}, cookies=admin_cookies
    )
    assert_error(response, 404, "Module not found")


@pytest.mark.asyncio
async def test_list_content_rejects_bad_module_id(client: AsyncClient, admin_cookies):
    """GET /api/content rejects a non-integer module_id."""
    response = await client.get(
        "/api/content", params={"module_id": "abc"}, cookies=admin_cookies
    )
    assert response.status_code == 422, response.text


# GET /api/content/{content_id}


@pytest.mark.asyncio
async def test_get_content(client: AsyncClient, world, educator_cookies, student_cookies):
    """GET /api/content/{id} returns one item the student can view."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id, 1), cookies=educator_cookies
    )
    assert created.status_code == 201, created.text
    response = await client.get(
        f"/api/content/{created.json()['id']}", cookies=student_cookies
    )
    assert response.status_code == 200, response.text
    assert_content_shape(response.json())
    assert response.json()["slide_data"] == "deck"


@pytest.mark.asyncio
async def test_get_content_forbidden(client: AsyncClient, world, admin_cookies, other_student_cookies):
    """GET /api/content/{id} rejects a student who is not enrolled."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id, 1), cookies=admin_cookies
    )
    response = await client.get(
        f"/api/content/{created.json()['id']}", cookies=other_student_cookies
    )
    assert_error(response, 403, "You cannot view this course")


@pytest.mark.asyncio
async def test_get_content_not_found(client: AsyncClient, admin_cookies):
    """GET /api/content/{id} returns 404 for a missing item."""
    response = await client.get(f"/api/content/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Content not found")


# PATCH /api/content/{content_id}


@pytest.mark.asyncio
async def test_update_content(client: AsyncClient, world, educator_cookies):
    """PATCH /api/content/{id} updates the title and strips whitespace."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id, 1), cookies=educator_cookies
    )
    response = await client.patch(
        f"/api/content/{created.json()['id']}",
        json={"title": "  Renamed  "},
        cookies=educator_cookies,
    )
    assert response.status_code == 200, response.text
    assert response.json()["title"] == "Renamed"
    assert response.json()["type"] == "slide"


@pytest.mark.asyncio
async def test_update_content_duplicate_position(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/content/{id} rejects a position another item already uses."""
    first = await client.post(
        "/api/slides", json=_slide(world.module_id, 1, "First"), cookies=admin_cookies
    )
    second = await client.post(
        "/api/slides", json=_slide(world.module_id, 2, "Second"), cookies=admin_cookies
    )
    response = await client.patch(
        f"/api/content/{second.json()['id']}",
        json={"position": 1},
        cookies=admin_cookies,
    )
    assert_error(response, 409, "A content item with this position already exists")
    assert first.status_code == 201


@pytest.mark.asyncio
async def test_update_content_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """PATCH /api/content/{id} rejects a student."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id, 1), cookies=admin_cookies
    )
    response = await client.patch(
        f"/api/content/{created.json()['id']}",
        json={"title": "Stolen"},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_update_content_forbidden_without_grant(
    client: AsyncClient, world, admin_cookies, other_educator_cookies
):
    """PATCH /api/content/{id} rejects an educator who has no edit grant."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id, 1), cookies=admin_cookies
    )
    response = await client.patch(
        f"/api/content/{created.json()['id']}",
        json={"title": "Stolen"},
        cookies=other_educator_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_update_content_rejects_blank_title(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/content/{id} rejects a blank title."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id, 1), cookies=admin_cookies
    )
    response = await client.patch(
        f"/api/content/{created.json()['id']}",
        json={"title": "   "},
        cookies=admin_cookies,
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_update_content_not_found(client: AsyncClient, admin_cookies):
    """PATCH /api/content/{id} returns 404 for a missing item."""
    response = await client.patch(
        f"/api/content/{MISSING_ID}", json={"title": "Nope"}, cookies=admin_cookies
    )
    assert_error(response, 404, "Content not found")


# DELETE /api/content/{content_id}


@pytest.mark.asyncio
async def test_delete_file_content_removes_stored_file(
    client: AsyncClient, world, admin_cookies, tmp_path
):
    """DELETE /api/content/{id} removes a file item and its stored bytes."""
    uploaded = await client.post(
        "/api/files", cookies=admin_cookies, **upload_parts(world.module_id)
    )
    assert uploaded.status_code == 201, uploaded.text
    content_id = uploaded.json()["id"]
    assert list(tmp_path.iterdir())
    response = await client.delete(f"/api/content/{content_id}", cookies=admin_cookies)
    assert response.status_code == 204, response.text
    assert list(tmp_path.iterdir()) == []
    follow = await client.get(f"/api/content/{content_id}", cookies=admin_cookies)
    assert_error(follow, 404, "Content not found")


@pytest.mark.asyncio
async def test_delete_content_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """DELETE /api/content/{id} rejects a student."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id, 1), cookies=admin_cookies
    )
    response = await client.delete(
        f"/api/content/{created.json()['id']}", cookies=student_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_delete_content_not_found(client: AsyncClient, admin_cookies):
    """DELETE /api/content/{id} returns 404 for a missing item."""
    response = await client.delete(f"/api/content/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Content not found")
