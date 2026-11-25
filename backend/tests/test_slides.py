"""
Contract-level tests for the /api/slides endpoints
"""

import pytest
from httpx import AsyncClient

from tests.helpers import MISSING_ID, assert_content_shape, assert_error, upload_parts


def _slide(module_id: int, position: int = 1, title: str = "Intro", data: str = "deck") -> dict:
    return {
        "module_id": module_id,
        "title": title,
        "position": position,
        "slide_data": data,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("POST", "/api/slides", _slide(1)),
        ("PATCH", "/api/slides/1", {"slide_data": "updated"}),
    ],
)
async def test_slide_routes_require_auth(client, method, path, json_body):
    """Slide routes reject a missing session."""
    response = await client.request(method, path, json=json_body)
    assert_error(response, 401, "Not authenticated")


# POST /api/slides


@pytest.mark.asyncio
async def test_create_slide(client: AsyncClient, world, educator_cookies):
    """POST /api/slides creates a slide and strips the title."""
    response = await client.post(
        "/api/slides",
        json=_slide(world.module_id, title="  Intro  ", data=""),
        cookies=educator_cookies,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert_content_shape(body)
    assert body["type"] == "slide"
    assert body["title"] == "Intro"
    assert body["slide_data"] == ""
    assert body["module_id"] == world.module_id
    assert body["position"] == 1


@pytest.mark.asyncio
async def test_create_slide_duplicate_position(client: AsyncClient, world, admin_cookies):
    """POST /api/slides rejects a position another content item already uses."""
    first = await client.post(
        "/api/slides", json=_slide(world.module_id), cookies=admin_cookies
    )
    assert first.status_code == 201, first.text
    response = await client.post(
        "/api/slides", json=_slide(world.module_id, title="Clash"), cookies=admin_cookies
    )
    assert_error(response, 409, "A content item with this position already exists")


@pytest.mark.asyncio
async def test_create_slide_unknown_module(client: AsyncClient, admin_cookies):
    """POST /api/slides returns 404 when the module does not exist."""
    response = await client.post(
        "/api/slides", json=_slide(MISSING_ID), cookies=admin_cookies
    )
    assert_error(response, 404, "Module not found")


@pytest.mark.asyncio
async def test_create_slide_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """POST /api/slides rejects a student."""
    response = await client.post(
        "/api/slides", json=_slide(world.module_id), cookies=student_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_create_slide_forbidden_without_grant(
    client: AsyncClient, world, other_educator_cookies
):
    """POST /api/slides rejects an educator who has no edit grant."""
    response = await client.post(
        "/api/slides", json=_slide(world.module_id), cookies=other_educator_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"title": "   ", "position": 1, "slide_data": "deck"},
        {"title": "Zero", "position": 0, "slide_data": "deck"},
        {"title": "Missing data", "position": 1},
    ],
)
async def test_create_slide_rejects_invalid_body(
    client: AsyncClient, world, admin_cookies, payload
):
    """POST /api/slides rejects a blank title, a bad position, and a missing deck."""
    response = await client.post(
        "/api/slides",
        json={"module_id": world.module_id, **payload},
        cookies=admin_cookies,
    )
    assert response.status_code == 422, response.text


# PATCH /api/slides/{content_id}


@pytest.mark.asyncio
async def test_update_slide(client: AsyncClient, world, educator_cookies):
    """PATCH /api/slides/{id} replaces the slide deck."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id), cookies=educator_cookies
    )
    response = await client.patch(
        f"/api/slides/{created.json()['id']}",
        json={"slide_data": "revised"},
        cookies=educator_cookies,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert_content_shape(body)
    assert body["slide_data"] == "revised"
    assert body["title"] == "Intro"


@pytest.mark.asyncio
async def test_update_slide_not_found_for_file(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/slides/{id} returns 404 when the content item is not a slide."""
    uploaded = await client.post(
        "/api/files", cookies=admin_cookies, **upload_parts(world.module_id)
    )
    assert uploaded.status_code == 201, uploaded.text
    response = await client.patch(
        f"/api/slides/{uploaded.json()['id']}",
        json={"slide_data": "revised"},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Slide not found")


@pytest.mark.asyncio
async def test_update_slide_missing_content(client: AsyncClient, admin_cookies):
    """PATCH /api/slides/{id} returns 404 when the content item does not exist."""
    response = await client.patch(
        f"/api/slides/{MISSING_ID}",
        json={"slide_data": "revised"},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Content not found")


@pytest.mark.asyncio
async def test_update_slide_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """PATCH /api/slides/{id} rejects a student."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id), cookies=admin_cookies
    )
    response = await client.patch(
        f"/api/slides/{created.json()['id']}",
        json={"slide_data": "revised"},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_update_slide_requires_slide_data(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/slides/{id} rejects a body without slide_data."""
    created = await client.post(
        "/api/slides", json=_slide(world.module_id), cookies=admin_cookies
    )
    response = await client.patch(
        f"/api/slides/{created.json()['id']}", json={}, cookies=admin_cookies
    )
    assert response.status_code == 422, response.text
