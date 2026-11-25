"""
Contract-level tests for the quiz, question, and choice endpoints
"""

import pytest
from httpx import AsyncClient

from tests.helpers import (
    MISSING_ID,
    assert_content_shape,
    assert_error,
    assert_question_shape,
)


SHAPE_ERROR = "A question needs at least two choices and exactly one correct choice"


def _quiz(module_id: int, position: int = 1, title: str = "Check") -> dict:
    return {"module_id": module_id, "title": title, "position": position}


def _question(text: str = "Capital of France?", position: int = 1, correct: int = 1) -> dict:
    return {
        "text": text,
        "position": position,
        "choices": [
            {"text": "Paris", "position": 1, "is_correct": correct == 1},
            {"text": "Rome", "position": 2, "is_correct": correct == 2},
        ],
    }


async def _create_quiz(client, world, cookies, position: int = 1):
    response = await client.post(
        "/api/quizzes", json=_quiz(world.module_id, position), cookies=cookies
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _create_question(client, quiz_id, cookies, **kwargs):
    response = await client.post(
        f"/api/quizzes/{quiz_id}/questions",
        json=_question(**kwargs),
        cookies=cookies,
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("POST", "/api/quizzes", _quiz(1)),
        ("POST", "/api/quizzes/1/questions", _question()),
        ("PATCH", "/api/questions/1", {"text": "Updated"}),
        ("DELETE", "/api/questions/1", None),
        (
            "POST",
            "/api/questions/1/choices",
            {"text": "Maybe", "position": 3, "is_correct": False},
        ),
        ("PATCH", "/api/choices/1", {"text": "Updated"}),
        ("DELETE", "/api/choices/1", None),
    ],
)
async def test_quiz_routes_require_auth(client, method, path, json_body):
    """Quiz routes reject a missing session."""
    kwargs = {} if json_body is None else {"json": json_body}
    response = await client.request(method, path, **kwargs)
    assert_error(response, 401, "Not authenticated")


# POST /api/quizzes


@pytest.mark.asyncio
async def test_create_quiz(client: AsyncClient, world, educator_cookies):
    """POST /api/quizzes creates an empty quiz and strips the title."""
    response = await client.post(
        "/api/quizzes",
        json=_quiz(world.module_id, title="  Check  "),
        cookies=educator_cookies,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert_content_shape(body)
    assert body["type"] == "quiz"
    assert body["title"] == "Check"
    assert body["questions"] == []
    assert body["module_id"] == world.module_id


@pytest.mark.asyncio
async def test_create_quiz_duplicate_position(client: AsyncClient, world, admin_cookies):
    """POST /api/quizzes rejects a position another content item already uses."""
    first = await _create_quiz(client, world, admin_cookies)
    response = await client.post(
        "/api/quizzes",
        json=_quiz(world.module_id, title="Clash"),
        cookies=admin_cookies,
    )
    assert_error(response, 409, "A content item with this position already exists")
    assert first["id"]


@pytest.mark.asyncio
async def test_create_quiz_unknown_module(client: AsyncClient, admin_cookies):
    """POST /api/quizzes returns 404 when the module does not exist."""
    response = await client.post(
        "/api/quizzes", json=_quiz(MISSING_ID), cookies=admin_cookies
    )
    assert_error(response, 404, "Module not found")


@pytest.mark.asyncio
async def test_create_quiz_forbidden_for_student(
    client: AsyncClient, world, student_cookies
):
    """POST /api/quizzes rejects a student."""
    response = await client.post(
        "/api/quizzes", json=_quiz(world.module_id), cookies=student_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_create_quiz_forbidden_without_grant(
    client: AsyncClient, world, other_educator_cookies
):
    """POST /api/quizzes rejects an educator who has no edit grant."""
    response = await client.post(
        "/api/quizzes", json=_quiz(world.module_id), cookies=other_educator_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"title": "   ", "position": 1},
        {"title": "Zero", "position": 0},
    ],
)
async def test_create_quiz_rejects_invalid_body(
    client: AsyncClient, world, admin_cookies, payload
):
    """POST /api/quizzes rejects a blank title and a non-positive position."""
    response = await client.post(
        "/api/quizzes",
        json={"module_id": world.module_id, **payload},
        cookies=admin_cookies,
    )
    assert response.status_code == 422, response.text


# POST /api/quizzes/{content_id}/questions


@pytest.mark.asyncio
async def test_create_question(client: AsyncClient, world, admin_cookies, student_cookies):
    """POST /api/quizzes/{id}/questions adds a question the content API returns."""
    quiz = await _create_quiz(client, world, admin_cookies)
    response = await client.post(
        f"/api/quizzes/{quiz['id']}/questions",
        json=_question(text="  Capital of France?  "),
        cookies=admin_cookies,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert_question_shape(body)
    assert body["text"] == "Capital of France?"
    assert body["position"] == 1
    correct = [choice for choice in body["choices"] if choice["is_correct"]]
    assert len(correct) == 1
    assert correct[0]["text"] == "Paris"

    fetched = await client.get(f"/api/content/{quiz['id']}", cookies=student_cookies)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["questions"][0]["id"] == body["id"]


@pytest.mark.asyncio
async def test_create_question_duplicate_position(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/quizzes/{id}/questions rejects a repeated question position."""
    quiz = await _create_quiz(client, world, admin_cookies)
    await _create_question(client, quiz["id"], admin_cookies)
    response = await client.post(
        f"/api/quizzes/{quiz['id']}/questions",
        json=_question(text="Second", position=1),
        cookies=admin_cookies,
    )
    assert_error(response, 409, "A question with this position already exists")


@pytest.mark.asyncio
async def test_create_question_on_slide(client: AsyncClient, world, admin_cookies):
    """POST /api/quizzes/{id}/questions returns 404 when the item is not a quiz."""
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
    response = await client.post(
        f"/api/quizzes/{slide.json()['id']}/questions",
        json=_question(),
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Quiz not found")


@pytest.mark.asyncio
async def test_create_question_missing_quiz(client: AsyncClient, admin_cookies):
    """POST /api/quizzes/{id}/questions returns 404 when the quiz does not exist."""
    response = await client.post(
        f"/api/quizzes/{MISSING_ID}/questions",
        json=_question(),
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Content not found")


@pytest.mark.asyncio
async def test_create_question_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """POST /api/quizzes/{id}/questions rejects a student."""
    quiz = await _create_quiz(client, world, admin_cookies)
    response = await client.post(
        f"/api/quizzes/{quiz['id']}/questions",
        json=_question(),
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (_question(correct=0), "exactly one choice must be correct"),
        (
            {
                "text": "Two right",
                "position": 1,
                "choices": [
                    {"text": "Paris", "position": 1, "is_correct": True},
                    {"text": "Rome", "position": 2, "is_correct": True},
                ],
            },
            "exactly one choice must be correct",
        ),
        (
            {
                "text": "Same spot",
                "position": 1,
                "choices": [
                    {"text": "Paris", "position": 1, "is_correct": True},
                    {"text": "Rome", "position": 1, "is_correct": False},
                ],
            },
            "choice positions must be unique",
        ),
        (
            {
                "text": "Only one",
                "position": 1,
                "choices": [{"text": "Paris", "position": 1, "is_correct": True}],
            },
            None,
        ),
        (_question(text="   "), None),
        (_question(position=0), None),
    ],
)
async def test_create_question_rejects_invalid_body(
    client: AsyncClient, world, admin_cookies, payload, message
):
    """POST /api/quizzes/{id}/questions rejects a question that is not well formed."""
    quiz = await _create_quiz(client, world, admin_cookies)
    response = await client.post(
        f"/api/quizzes/{quiz['id']}/questions",
        json=payload,
        cookies=admin_cookies,
    )
    assert response.status_code == 422, response.text
    if message is not None:
        assert message in response.text
    fetched = await client.get(f"/api/content/{quiz['id']}", cookies=admin_cookies)
    assert fetched.json()["questions"] == []


# PATCH /api/questions/{question_id}


@pytest.mark.asyncio
async def test_update_question(client: AsyncClient, world, admin_cookies):
    """PATCH /api/questions/{id} updates text and can keep the same position."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    response = await client.patch(
        f"/api/questions/{question['id']}",
        json={"text": "  Revised  ", "position": 1},
        cookies=admin_cookies,
    )
    assert response.status_code == 200, response.text
    assert response.json()["text"] == "Revised"
    assert len(response.json()["choices"]) == 2


@pytest.mark.asyncio
async def test_update_question_duplicate_position(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/questions/{id} rejects a position another question already uses."""
    quiz = await _create_quiz(client, world, admin_cookies)
    await _create_question(client, quiz["id"], admin_cookies)
    second = await _create_question(
        client, quiz["id"], admin_cookies, text="Second", position=2
    )
    response = await client.patch(
        f"/api/questions/{second['id']}",
        json={"position": 1},
        cookies=admin_cookies,
    )
    assert_error(response, 409, "A question with this position already exists")


@pytest.mark.asyncio
async def test_update_question_not_found(client: AsyncClient, admin_cookies):
    """PATCH /api/questions/{id} returns 404 for a missing question."""
    response = await client.patch(
        f"/api/questions/{MISSING_ID}",
        json={"text": "Nope"},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Question not found")


@pytest.mark.asyncio
async def test_update_question_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """PATCH /api/questions/{id} rejects a student."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    response = await client.patch(
        f"/api/questions/{question['id']}",
        json={"text": "Stolen"},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


# DELETE /api/questions/{question_id}


@pytest.mark.asyncio
async def test_delete_question(client: AsyncClient, world, admin_cookies):
    """DELETE /api/questions/{id} removes the question from the quiz."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    response = await client.delete(
        f"/api/questions/{question['id']}", cookies=admin_cookies
    )
    assert response.status_code == 204, response.text
    fetched = await client.get(f"/api/content/{quiz['id']}", cookies=admin_cookies)
    assert fetched.json()["questions"] == []


@pytest.mark.asyncio
async def test_delete_question_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """DELETE /api/questions/{id} rejects a student."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    response = await client.delete(
        f"/api/questions/{question['id']}", cookies=student_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_delete_question_not_found(client: AsyncClient, admin_cookies):
    """DELETE /api/questions/{id} returns 404 for a missing question."""
    response = await client.delete(f"/api/questions/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Question not found")


# POST /api/questions/{question_id}/choices


@pytest.mark.asyncio
async def test_create_choice_can_become_the_correct_answer(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/questions/{id}/choices can take over the single correct flag."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    response = await client.post(
        f"/api/questions/{question['id']}/choices",
        json={"text": "Lyon", "position": 3, "is_correct": True},
        cookies=admin_cookies,
    )
    assert response.status_code == 201, response.text
    assert response.json()["is_correct"] is True
    fetched = await client.get(f"/api/content/{quiz['id']}", cookies=admin_cookies)
    correct = [
        choice
        for choice in fetched.json()["questions"][0]["choices"]
        if choice["is_correct"]
    ]
    assert [choice["text"] for choice in correct] == ["Lyon"]


@pytest.mark.asyncio
async def test_create_choice_duplicate_position(
    client: AsyncClient, world, admin_cookies
):
    """POST /api/questions/{id}/choices rejects a repeated choice position."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    response = await client.post(
        f"/api/questions/{question['id']}/choices",
        json={"text": "Lyon", "position": 1, "is_correct": False},
        cookies=admin_cookies,
    )
    assert_error(response, 409, "A choice with this position already exists")


@pytest.mark.asyncio
async def test_create_choice_not_found(client: AsyncClient, admin_cookies):
    """POST /api/questions/{id}/choices returns 404 for a missing question."""
    response = await client.post(
        f"/api/questions/{MISSING_ID}/choices",
        json={"text": "Lyon", "position": 1, "is_correct": False},
        cookies=admin_cookies,
    )
    assert_error(response, 404, "Question not found")


@pytest.mark.asyncio
async def test_create_choice_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """POST /api/questions/{id}/choices rejects a student."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    response = await client.post(
        f"/api/questions/{question['id']}/choices",
        json={"text": "Lyon", "position": 3, "is_correct": False},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


# PATCH /api/choices/{choice_id}


@pytest.mark.asyncio
async def test_update_choice(client: AsyncClient, world, admin_cookies):
    """PATCH /api/choices/{id} updates text and strips whitespace."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    choice_id = question["choices"][0]["id"]
    response = await client.patch(
        f"/api/choices/{choice_id}",
        json={"text": "  Paris, France  "},
        cookies=admin_cookies,
    )
    assert response.status_code == 200, response.text
    assert response.json()["text"] == "Paris, France"
    assert response.json()["is_correct"] is True


@pytest.mark.asyncio
async def test_update_choice_cannot_clear_the_only_correct_answer(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/choices/{id} rejects a change that leaves no correct choice."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    correct_id = next(
        choice["id"] for choice in question["choices"] if choice["is_correct"]
    )
    response = await client.patch(
        f"/api/choices/{correct_id}",
        json={"is_correct": False},
        cookies=admin_cookies,
    )
    assert_error(response, 422, SHAPE_ERROR)
    fetched = await client.get(f"/api/content/{quiz['id']}", cookies=admin_cookies)
    correct = [
        choice
        for choice in fetched.json()["questions"][0]["choices"]
        if choice["is_correct"]
    ]
    assert [choice["id"] for choice in correct] == [correct_id]


@pytest.mark.asyncio
async def test_update_choice_duplicate_position(
    client: AsyncClient, world, admin_cookies
):
    """PATCH /api/choices/{id} rejects a position another choice already uses."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    wrong_id = next(
        choice["id"] for choice in question["choices"] if not choice["is_correct"]
    )
    response = await client.patch(
        f"/api/choices/{wrong_id}", json={"position": 1}, cookies=admin_cookies
    )
    assert_error(response, 409, "A choice with this position already exists")


@pytest.mark.asyncio
async def test_update_choice_not_found(client: AsyncClient, admin_cookies):
    """PATCH /api/choices/{id} returns 404 for a missing choice."""
    response = await client.patch(
        f"/api/choices/{MISSING_ID}", json={"text": "Nope"}, cookies=admin_cookies
    )
    assert_error(response, 404, "Choice not found")


@pytest.mark.asyncio
async def test_update_choice_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """PATCH /api/choices/{id} rejects a student."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    response = await client.patch(
        f"/api/choices/{question['choices'][0]['id']}",
        json={"text": "Stolen"},
        cookies=student_cookies,
    )
    assert_error(response, 403, "You cannot edit this course")


# DELETE /api/choices/{choice_id}


@pytest.mark.asyncio
async def test_delete_choice_keeps_a_valid_question(
    client: AsyncClient, world, admin_cookies
):
    """DELETE /api/choices/{id} can remove an extra wrong choice, not the last pair."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    wrong_id = next(
        choice["id"] for choice in question["choices"] if not choice["is_correct"]
    )
    blocked = await client.delete(f"/api/choices/{wrong_id}", cookies=admin_cookies)
    assert_error(blocked, 422, SHAPE_ERROR)

    added = await client.post(
        f"/api/questions/{question['id']}/choices",
        json={"text": "Lyon", "position": 3, "is_correct": False},
        cookies=admin_cookies,
    )
    assert added.status_code == 201, added.text
    response = await client.delete(
        f"/api/choices/{added.json()['id']}", cookies=admin_cookies
    )
    assert response.status_code == 204, response.text
    fetched = await client.get(f"/api/content/{quiz['id']}", cookies=admin_cookies)
    assert len(fetched.json()["questions"][0]["choices"]) == 2


@pytest.mark.asyncio
async def test_delete_choice_forbidden_for_student(
    client: AsyncClient, world, admin_cookies, student_cookies
):
    """DELETE /api/choices/{id} rejects a student."""
    quiz = await _create_quiz(client, world, admin_cookies)
    question = await _create_question(client, quiz["id"], admin_cookies)
    response = await client.delete(
        f"/api/choices/{question['choices'][1]['id']}", cookies=student_cookies
    )
    assert_error(response, 403, "You cannot edit this course")


@pytest.mark.asyncio
async def test_delete_choice_not_found(client: AsyncClient, admin_cookies):
    """DELETE /api/choices/{id} returns 404 for a missing choice."""
    response = await client.delete(f"/api/choices/{MISSING_ID}", cookies=admin_cookies)
    assert_error(response, 404, "Choice not found")
