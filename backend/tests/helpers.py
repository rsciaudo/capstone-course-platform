"""Shared assertions and request helpers for API contract tests."""

from httpx import AsyncClient, Response

PASSWORD = "password"
MISSING_ID = 999_999

PDF_BYTES = b"%PDF-1.4 test\n"
PNG_BYTES = b"\x89PNG\r\n\x1a\nfake"

USER_KEYS = {
    "id",
    "name",
    "username",
    "role",
    "group_id",
    "created_at",
    "updated_at",
}
GROUP_KEYS = {"id", "name", "created_by", "created_at", "updated_at"}
COURSE_KEYS = {"id", "name", "group_id", "created_by", "created_at", "updated_at"}
MODULE_KEYS = {"id", "course_id", "name", "position", "created_at", "updated_at"}
ENROLLMENT_KEYS = {"id", "user_id", "course_id", "created_at", "updated_at"}
GRANT_KEYS = {"id", "user_id", "course_id", "created_at", "updated_at"}
FILE_KEYS = {
    "id",
    "module_id",
    "type",
    "title",
    "position",
    "filename",
    "content_type",
}
QUIZ_KEYS = {"id", "module_id", "type", "title", "position", "questions"}
SLIDE_KEYS = {"id", "module_id", "type", "title", "position", "slide_data"}
QUESTION_KEYS = {"id", "text", "position", "choices"}
CHOICE_KEYS = {"id", "text", "position", "is_correct"}


def assert_keys(data: dict, keys: set[str]) -> None:
    assert set(data) == keys


def assert_user_shape(data: dict) -> None:
    assert_keys(data, USER_KEYS)
    assert "password" not in data
    assert "password_hash" not in data


def assert_group_shape(data: dict) -> None:
    assert_keys(data, GROUP_KEYS)


def assert_course_shape(data: dict) -> None:
    assert_keys(data, COURSE_KEYS)


def assert_module_shape(data: dict) -> None:
    assert_keys(data, MODULE_KEYS)


def assert_enrollment_shape(data: dict) -> None:
    assert_keys(data, ENROLLMENT_KEYS)


def assert_grant_shape(data: dict) -> None:
    assert_keys(data, GRANT_KEYS)


def assert_choice_shape(data: dict) -> None:
    assert_keys(data, CHOICE_KEYS)


def assert_question_shape(data: dict) -> None:
    assert_keys(data, QUESTION_KEYS)
    for choice in data["choices"]:
        assert_choice_shape(choice)


def assert_content_shape(data: dict) -> None:
    if data["type"] == "file":
        assert_keys(data, FILE_KEYS)
    elif data["type"] == "quiz":
        assert_keys(data, QUIZ_KEYS)
        for question in data["questions"]:
            assert_question_shape(question)
    elif data["type"] == "slide":
        assert_keys(data, SLIDE_KEYS)
    else:
        raise AssertionError(f"unexpected content type {data['type']}")


def assert_error(response: Response, status_code: int, detail: str) -> None:
    assert response.status_code == status_code, response.text
    assert response.json()["detail"] == detail


async def login(
    client: AsyncClient, username: str, password: str = PASSWORD
) -> dict[str, str]:
    """Log in and return the session cookie without leaving it on the client."""
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    cookies = {key: value for key, value in response.cookies.items()}
    if not cookies:
        cookies = {key: value for key, value in client.cookies.items()}
    client.cookies.clear()
    assert "session" in cookies
    return cookies


def upload_parts(
    module_id: int,
    *,
    title: str = "Notes",
    position: int = 1,
    filename: str = "notes.pdf",
    content: bytes = PDF_BYTES,
    content_type: str = "application/pdf",
) -> dict:
    return {
        "data": {
            "module_id": str(module_id),
            "title": title,
            "position": str(position),
        },
        "files": {"file": (filename, content, content_type)},
    }
