"""
Contract-level tests for the /api/groups endpoints
"""

import pytest
from httpx import AsyncClient

from app.models import Group
from tests.helpers import MISSING_ID, assert_error, assert_group_shape


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/groups", None),
        ("GET", "/api/groups/1", None),
        ("POST", "/api/groups", {"name": "Nope"}),
        ("PATCH", "/api/groups/1", {"name": "Nope"}),
        ("DELETE", "/api/groups/1", None),
    ],
)
async def test_group_routes_require_auth(client, method, path, json_body):
    """Group routes reject a missing session."""
    kwargs = {} if json_body is None else {"json": json_body}
    response = await client.request(method, path, **kwargs)
    assert_error(response, 401, "Not authenticated")


# GET /api/groups


@pytest.mark.asyncio
async def test_list_groups_scopes_by_role(
    client: AsyncClient,
    world,
    super_cookies,
    admin_cookies,
    other_admin_cookies,
    educator_cookies,
    student_cookies,
):
    """GET /api/groups returns the groups each role is allowed to see."""
    super_response = await client.get("/api/groups", cookies=super_cookies)
    assert super_response.status_code == 200, super_response.text
    super_ids = {group["id"] for group in super_response.json()}
    assert super_ids == {world.group_id, world.other_group_id}
    for group in super_response.json():
        assert_group_shape(group)

    admin_response = await client.get("/api/groups", cookies=admin_cookies)
    assert admin_response.status_code == 200, admin_response.text
    assert {group["id"] for group in admin_response.json()} == {world.group_id}

    other_response = await client.get("/api/groups", cookies=other_admin_cookies)
    assert {group["id"] for group in other_response.json()} == {world.other_group_id}

    educator_response = await client.get("/api/groups", cookies=educator_cookies)
    assert {group["id"] for group in educator_response.json()} == {world.group_id}

    student_response = await client.get("/api/groups", cookies=student_cookies)
    assert {group["id"] for group in student_response.json()} == {world.group_id}


# GET /api/groups/{group_id}


@pytest.mark.asyncio
async def test_get_group(client: AsyncClient, world, student_cookies):
    """GET /api/groups/{id} returns the caller's group."""
    response = await client.get(f"/api/groups/{world.group_id}", cookies=student_cookies)
    assert response.status_code == 200, response.text
    body = response.json()
    assert_group_shape(body)
    assert body["id"] == world.group_id
    assert body["name"] == "Demo group"
    assert body["created_by"] == world.admin.id


@pytest.mark.asyncio
async def test_get_group_forbidden_for_other_admin(
    client: AsyncClient, world, other_admin_cookies
):
    """GET /api/groups/{id} hides a group created by someone else."""
    response = await client.get(
        f"/api/groups/{world.group_id}", cookies=other_admin_cookies
    )
    assert_error(response, 403, "You cannot view this group")


@pytest.mark.asyncio
async def test_get_group_forbidden_for_other_groups_student(
    client: AsyncClient, world, outsider_student_cookies
):
    """GET /api/groups/{id} hides a group the student does not belong to."""
    response = await client.get(
        f"/api/groups/{world.group_id}", cookies=outsider_student_cookies
    )
    assert_error(response, 403, "You cannot view this group")


@pytest.mark.asyncio
async def test_super_user_can_view_any_group(
    client: AsyncClient, world, super_cookies
):
    """GET /api/groups/{id} allows a super-user to open any group."""
    response = await client.get(
        f"/api/groups/{world.other_group_id}", cookies=super_cookies
    )
    assert response.status_code == 200, response.text
    assert response.json()["id"] == world.other_group_id


@pytest.mark.asyncio
async def test_get_group_without_creator_is_hidden_from_admin(
    client: AsyncClient, db_session, admin_cookies, super_cookies
):
    """A group with no creator is visible to a super-user only."""
    group = Group(name="Orphan", created_by=None)
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    hidden = await client.get(f"/api/groups/{group.id}", cookies=admin_cookies)
    assert_error(hidden, 403, "You cannot view this group")
    visible = await client.get(f"/api/groups/{group.id}", cookies=super_cookies)
    assert visible.status_code == 200, visible.text
    assert visible.json()["created_by"] is None


@pytest.mark.asyncio
async def test_get_group_not_found(client: AsyncClient, admin_cookies):
    """GET /api/groups/{id} returns 404 for a missing group."""
    response = await client.get(f"/api/groups/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Group not found")


@pytest.mark.asyncio
async def test_get_group_rejects_string_id(client: AsyncClient, admin_cookies):
    """GET /api/groups/{id} rejects a non-integer id."""
    response = await client.get("/api/groups/nope", cookies=admin_cookies)
    assert response.status_code == 422, response.text


# POST /api/groups


@pytest.mark.asyncio
async def test_create_group(client: AsyncClient, world, admin_cookies):
    """POST /api/groups lets an admin create a group they own."""
    response = await client.post(
        "/api/groups",
        json={"name": "  New Group  "},
        cookies=admin_cookies,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert_group_shape(body)
    assert body["name"] == "New Group"
    assert body["created_by"] == world.admin.id


@pytest.mark.asyncio
async def test_super_user_can_create_group(client: AsyncClient, world, super_cookies):
    """POST /api/groups lets a super-user create a group."""
    response = await client.post(
        "/api/groups", json={"name": "Super Group"}, cookies=super_cookies
    )
    assert response.status_code == 201, response.text
    assert response.json()["created_by"] == world.super_user.id


@pytest.mark.asyncio
async def test_create_group_forbidden(
    client: AsyncClient, educator_cookies, student_cookies
):
    """POST /api/groups rejects educators and students."""
    for cookies in (educator_cookies, student_cookies):
        response = await client.post(
            "/api/groups",
            json={"name": "Denied"},
            cookies=cookies,
        )
        assert_error(response, 403, "You cannot create groups")


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["", "   "])
async def test_create_group_rejects_blank_name(client: AsyncClient, admin_cookies, name):
    """POST /api/groups rejects a blank name."""
    response = await client.post("/api/groups", json={"name": name}, cookies=admin_cookies)
    assert response.status_code == 422, response.text


# PATCH /api/groups/{group_id}


@pytest.mark.asyncio
async def test_update_group(client: AsyncClient, world, admin_cookies):
    """PATCH /api/groups/{id} lets the creator rename the group."""
    response = await client.patch(
        f"/api/groups/{world.group_id}",
        json={"name": "  Renamed  "},
        cookies=admin_cookies,
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Renamed"


@pytest.mark.asyncio
async def test_update_group_empty_body(client: AsyncClient, world, admin_cookies):
    """PATCH /api/groups/{id} with no fields leaves the name unchanged."""
    response = await client.patch(
        f"/api/groups/{world.group_id}", json={}, cookies=admin_cookies
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Demo group"


@pytest.mark.asyncio
async def test_super_user_can_rename_another_admins_group(
    client: AsyncClient, world, super_cookies
):
    """PATCH /api/groups/{id} lets a super-user edit any group."""
    response = await client.patch(
        f"/api/groups/{world.other_group_id}",
        json={"name": "Renamed by super"},
        cookies=super_cookies,
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Renamed by super"


@pytest.mark.asyncio
async def test_update_group_forbidden_for_other_admin(
    client: AsyncClient, world, other_admin_cookies
):
    """PATCH /api/groups/{id} rejects an admin who did not create the group."""
    response = await client.patch(
        f"/api/groups/{world.group_id}",
        json={"name": "Stolen"},
        cookies=other_admin_cookies,
    )
    assert_error(response, 403, "You cannot edit this group")


@pytest.mark.asyncio
async def test_update_group_forbidden_for_educator(
    client: AsyncClient, world, educator_cookies
):
    """PATCH /api/groups/{id} rejects an educator, including their own group."""
    response = await client.patch(
        f"/api/groups/{world.group_id}",
        json={"name": "Stolen"},
        cookies=educator_cookies,
    )
    assert_error(response, 403, "You cannot edit this group")


@pytest.mark.asyncio
async def test_update_group_not_found(client: AsyncClient, admin_cookies):
    """PATCH /api/groups/{id} returns 404 for a missing group."""
    response = await client.patch(
        f"/api/groups/{MISSING_ID}", json={"name": "Nope"}, cookies=admin_cookies
    )
    assert_error(response, 404, "Group not found")


@pytest.mark.asyncio
async def test_update_group_rejects_blank_name(client: AsyncClient, world, admin_cookies):
    """PATCH /api/groups/{id} rejects a blank name."""
    response = await client.patch(
        f"/api/groups/{world.group_id}", json={"name": "   "}, cookies=admin_cookies
    )
    assert response.status_code == 422, response.text


# DELETE /api/groups/{group_id}


@pytest.mark.asyncio
async def test_delete_group(client: AsyncClient, admin_cookies, super_cookies):
    """DELETE /api/groups/{id} removes an empty group."""
    created = await client.post(
        "/api/groups", json={"name": "Temporary"}, cookies=admin_cookies
    )
    assert created.status_code == 201, created.text
    group_id = created.json()["id"]
    response = await client.delete(f"/api/groups/{group_id}", cookies=super_cookies)
    assert response.status_code == 204, response.text
    follow = await client.get(f"/api/groups/{group_id}", cookies=super_cookies)
    assert_error(follow, 404, "Group not found")


@pytest.mark.asyncio
async def test_delete_group_still_referenced(client: AsyncClient, world, admin_cookies):
    """DELETE /api/groups/{id} returns 409 while users or courses still reference it."""
    response = await client.delete(
        f"/api/groups/{world.group_id}", cookies=admin_cookies
    )
    assert_error(response, 409, "Group is still referenced by another record")


@pytest.mark.asyncio
async def test_delete_group_forbidden(client: AsyncClient, world, educator_cookies):
    """DELETE /api/groups/{id} rejects a caller who cannot edit the group."""
    response = await client.delete(
        f"/api/groups/{world.group_id}", cookies=educator_cookies
    )
    assert_error(response, 403, "You cannot edit this group")


@pytest.mark.asyncio
async def test_delete_group_not_found(client: AsyncClient, admin_cookies):
    """DELETE /api/groups/{id} returns 404 for a missing group."""
    response = await client.delete(f"/api/groups/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Group not found")
