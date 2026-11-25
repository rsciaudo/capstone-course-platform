"""
Contract-level tests for the /api/files endpoints
"""

import pytest
from httpx import AsyncClient

from tests.helpers import (
    MISSING_ID,
    PDF_BYTES,
    PNG_BYTES,
    assert_content_shape,
    assert_error,
    upload_parts,
)


@pytest.mark.asyncio
async def test_file_routes_require_auth(client: AsyncClient):
    """File routes reject a missing session."""
    created = await client.post("/api/files", **upload_parts(1))
    assert_error(created, 401, "Not authenticated")
    downloaded = await client.get("/api/files/1")
    assert_error(downloaded, 401, "Not authenticated")
    replaced = await client.patch(
        "/api/files/1",
        files={"file": ("notes.pdf", PDF_BYTES, "application/pdf")},
    )
    assert_error(replaced, 401, "Not authenticated")


# POST /api/files


@pytest.mark.asyncio
async def test_create_and_download_file(
    client: AsyncClient, world, educator_cookies, student_cookies
):
    """POST /api/files stores an upload, and an enrolled student can download it."""
    response = await client.post(
        "/api/files",
        cookies=educator_cookies,
        **upload_parts(world.module_id, title="  Notes  ", filename="../secret.pdf"),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert_content_shape(body)
    assert body["type"] == "file"
    assert body["title"] == "Notes"
    assert body["filename"] == "secret.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["module_id"] == world.module_id

    downloaded = await client.get(f"/api/files/{body['id']}", cookies=student_cookies)
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.content == PDF_BYTES
    assert downloaded.headers["content-type"].startswith("application/pdf")
    assert "secret.pdf" in downloaded.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_create_file_duplicate_position_removes_new_bytes(
    client: AsyncClient, world, admin_cookies, tmp_path
):
    """POST /api/files rolls back the new file when the position is already used."""
    created = await client.post(
        "/api/files", cookies=admin_cookies, **upload_parts(world.module_id)
    )
    assert created.status_code == 201, created.text
    kept = {path.name for path in tmp_path.iterdir()}
    assert len(kept) == 1
    conflict = await client.post(
        "/api/files",
        cookies=admin_cookies,
        **upload_parts(world.module_id, filename="other.pdf"),
    )
    assert_error(conflict, 409, "A content item with this position already exists")
    assert {path.name for path in tmp_path.iterdir()} == kept


@pytest.mark.asyncio
async def test_create_file_unknown_module(client: AsyncClient, admin_cookies, tmp_path):
    """POST /api/files returns 404 when the module does not exist and writes nothing."""
    response = await client.post(
        "/api/files", cookies=admin_cookies, **upload_parts(MISSING_ID)
    )
    assert_error(response, 404, "Module not found")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_create_file_forbidden_for_student(
    client: AsyncClient, world, student_cookies, tmp_path
):
    """POST /api/files rejects a student and writes nothing."""
    response = await client.post(
        "/api/files", cookies=student_cookies, **upload_parts(world.module_id)
    )
    assert_error(response, 403, "You cannot edit this course")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_create_file_forbidden_without_grant(
    client: AsyncClient, world, other_educator_cookies
):
    """POST /api/files rejects an educator who has no edit grant."""
    response = await client.post(
        "/api/files",
        cookies=other_educator_cookies,
        **upload_parts(world.module_id),
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_create_file_rejects_empty_upload(
    client: AsyncClient, world, admin_cookies, tmp_path
):
    """POST /api/files rejects an empty file."""
    response = await client.post(
        "/api/files",
        cookies=admin_cookies,
        **upload_parts(world.module_id, content=b""),
    )
    assert_error(response, 422, "File is empty")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_create_file_rejects_disallowed_type(
    client: AsyncClient, world, admin_cookies, tmp_path
):
    """POST /api/files rejects a file that is not an image or PDF."""
    response = await client.post(
        "/api/files",
        cookies=admin_cookies,
        **upload_parts(world.module_id, content=b"hello", content_type="text/plain"),
    )
    assert_error(response, 422, "File must be an image or PDF")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_create_file_rejects_blank_title(
    client: AsyncClient, world, admin_cookies, tmp_path
):
    """POST /api/files rejects a blank title before writing the file."""
    response = await client.post(
        "/api/files",
        cookies=admin_cookies,
        **upload_parts(world.module_id, title="   "),
    )
    assert response.status_code == 422, response.text
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_create_file_rejects_non_positive_position(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/files rejects position 0."""
    response = await client.post(
        "/api/files",
        cookies=admin_cookies,
        **upload_parts(world.module_id, position=0),
    )
    assert response.status_code == 422, response.text


# GET /api/files/{content_id}


@pytest.mark.asyncio
async def test_download_file_forbidden(
    client: AsyncClient, world, admin_cookies, other_student_cookies, other_admin_cookies
):
    """GET /api/files/{id} rejects callers who cannot view the course."""
    uploaded = await client.post(
        "/api/files", cookies=admin_cookies, **upload_parts(world.module_id)
    )
    content_id = uploaded.json()["id"]
    for cookies in (other_student_cookies, other_admin_cookies):
        response = await client.get(f"/api/files/{content_id}", cookies=cookies)
        assert_error(response, 403, "You cannot view this course")


@pytest.mark.asyncio
async def test_download_file_not_found_for_slide(
    client: AsyncClient, world, admin_cookies
):
    """GET /api/files/{id} returns 404 when the content item is not a file."""
    slide = await client.post(
        "/api/slides",
        json={
            "module_id": world.module_id,
            "title": "Intro",
            "position": 1,
            "slide_data": "deck",
        },
        cookies=admin_cookies,
    )
    assert slide.status_code == 201, slide.text
    response = await client.get(f"/api/files/{slide.json()['id']}", cookies=admin_cookies)
    assert_error(response, 404, "File not found")


@pytest.mark.asyncio
async def test_download_file_missing_content(client: AsyncClient, admin_cookies):
    """GET /api/files/{id} returns 404 when the content item does not exist."""
    response = await client.get(f"/api/files/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Content not found")


# PATCH /api/files/{content_id}


@pytest.mark.asyncio
async def test_replace_file(client: AsyncClient, world, admin_cookies, student_cookies, tmp_path):
    """PATCH /api/files/{id} replaces the stored bytes and removes the old file."""
    uploaded = await client.post(
        "/api/files", cookies=admin_cookies, **upload_parts(world.module_id)
    )
    assert uploaded.status_code == 201, uploaded.text
    content_id = uploaded.json()["id"]
    original = {path.name for path in tmp_path.iterdir()}

    response = await client.patch(
        f"/api/files/{content_id}",
        files={"file": ("photo.png", PNG_BYTES, "image/png")},
        cookies=admin_cookies,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert_content_shape(body)
    assert body["filename"] == "photo.png"
    assert body["content_type"] == "image/png"
    replaced = {path.name for path in tmp_path.iterdir()}
    assert len(replaced) == 1
    assert original.isdisjoint(replaced)

    downloaded = await client.get(f"/api/files/{content_id}", cookies=student_cookies)
    assert downloaded.content == PNG_BYTES


@pytest.mark.asyncio
async def test_replace_file_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """PATCH /api/files/{id} rejects a student."""
    uploaded = await client.post(
        "/api/files", cookies=admin_cookies, **upload_parts(world.module_id)
    )
    response = await client.patch(
        f"/api/files/{uploaded.json()['id']}",
        files={"file": ("photo.png", PNG_BYTES, "image/png")},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_replace_file_not_found_for_slide(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/files/{id} returns 404 when the content item is not a file."""
    slide = await client.post(
        "/api/slides",
        json={
            "module_id": world.module_id,
            "title": "Intro",
            "position": 1,
            "slide_data": "deck",
        },
        cookies=admin_cookies,
    )
    response = await client.patch(
        f"/api/files/{slide.json()['id']}",
        files={"file": ("photo.png", PNG_BYTES, "image/png")},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "File not found")


@pytest.mark.asyncio
async def test_replace_file_rejects_empty_upload(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/files/{id} rejects an empty replacement."""
    uploaded = await client.post(
        "/api/files", cookies=admin_cookies, **upload_parts(world.module_id)
    )
    response = await client.patch(
        f"/api/files/{uploaded.json()['id']}",
        files={"file": ("notes.pdf", b"", "application/pdf")},
        cookies=admin_cookies,
    )
    assert_error(response, 422, "File is empty")
