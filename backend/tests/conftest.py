"""
Pytest fixtures for API contract tests.

Postgres database `platform_test` is created on the session loop. Each test
truncates that database. The development database is never used.
"""

import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _load_project_env() -> None:
    if not _ENV_PATH.is_file():
        return
    for raw in _ENV_PATH.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_project_env()
os.environ["POSTGRES_DB"] = "platform_test"
os.environ["SESSION_SECRET"] = "test-secret"
if not os.environ.get("POSTGRES_HOST"):
    os.environ["POSTGRES_HOST"] = "localhost"
os.environ["FILE_STORAGE_DIR"] = "/tmp/platform-tests"

_missing = [
    name
    for name in ("POSTGRES_USER", "POSTGRES_PASSWORD")
    if not os.environ.get(name)
]
if _missing:
    raise RuntimeError(
        "Tests need POSTGRES_USER and POSTGRES_PASSWORD in the environment or in "
        f"{_ENV_PATH}. Missing: {', '.join(_missing)}"
    )

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app.database import SessionLocal, database_url, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Base,
    Course,
    CourseEditGrant,
    CourseEnrollment,
    Group,
    Module,
    User,
)
from app.passwords import hash_password  # noqa: E402
from tests.helpers import PASSWORD, login  # noqa: E402


@asynccontextmanager
async def _skip_startup(_app):
    """Do not seed users or dispose the shared engine during HTTP tests."""
    yield


app.router.lifespan_context = _skip_startup


@dataclass(frozen=True)
class Account:
    id: int
    username: str
    role: str
    group_id: int | None


@dataclass(frozen=True)
class World:
    super_user: Account
    admin: Account
    other_admin: Account
    educator: Account
    other_educator: Account
    student: Account
    other_student: Account
    outsider_educator: Account
    outsider_student: Account
    group_id: int
    other_group_id: int
    course_id: int
    module_id: int
    enrollment_id: int
    edit_grant_id: int


def _admin_database_url() -> str:
    user = quote_plus(os.environ["POSTGRES_USER"])
    password = quote_plus(os.environ["POSTGRES_PASSWORD"])
    host = os.environ["POSTGRES_HOST"]
    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/postgres"


async def _ensure_test_database() -> None:
    if os.environ["POSTGRES_DB"] != "platform_test":
        raise RuntimeError("Refusing to create a database other than platform_test")
    admin_engine = create_async_engine(
        _admin_database_url(),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        async with admin_engine.connect() as connection:
            exists = await connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'platform_test'")
            )
            if exists.scalar() is None:
                await connection.execute(text("CREATE DATABASE platform_test"))
    finally:
        await admin_engine.dispose()


async def _truncate() -> None:
    names = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    async with engine.begin() as connection:
        await connection.execute(
            text(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE")
        )


async def _account(session, password_hash, **kwargs) -> Account:
    user = User(password_hash=password_hash, **kwargs)
    session.add(user)
    await session.flush()
    return Account(user.id, user.username, user.role, user.group_id)


@pytest.fixture(scope="session")
def password_hash():
    """Hash the shared test password once. Argon2 is too slow to repeat per user."""
    return hash_password(PASSWORD)

async def _reset_schema() -> None:
    reset_engine = create_async_engine(
        database_url(),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        async with reset_engine.connect() as connection:
            await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
    finally:
        await reset_engine.dispose()
    await engine.dispose()

@pytest_asyncio.fixture(scope="session")
async def initialized_test_db():
    if not database_url().endswith("/platform_test"):
        raise RuntimeError("Refusing to reset a database other than platform_test")
    await _ensure_test_database()
    await _reset_schema()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(initialized_test_db, tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_DIR", str(tmp_path))
    await _truncate()
    yield


@pytest_asyncio.fixture
async def client(test_db):
    """HTTP client. ASGITransport does not run the app lifespan."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session(test_db):
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def world(test_db, password_hash) -> World:
    """Roles, two groups, one course, one module, one enrollment, and one edit grant."""
    async with SessionLocal() as session:
        super_user = await _account(
            session,
            password_hash,
            name="Super User",
            username="super",
            role="super-user",
            group_id=None,
        )
        admin = await _account(
            session,
            password_hash,
            name="Admin",
            username="admin",
            role="admin",
            group_id=None,
        )
        other_admin = await _account(
            session,
            password_hash,
            name="Other Admin",
            username="other-admin",
            role="admin",
            group_id=None,
        )

        group = Group(name="Demo group", created_by=admin.id)
        other_group = Group(name="Other group", created_by=other_admin.id)
        session.add_all([group, other_group])
        await session.flush()

        educator = await _account(
            session,
            password_hash,
            name="Educator",
            username="educator",
            role="educator",
            group_id=group.id,
        )
        other_educator = await _account(
            session,
            password_hash,
            name="Other Educator",
            username="other-educator",
            role="educator",
            group_id=group.id,
        )
        student = await _account(
            session,
            password_hash,
            name="Student",
            username="student",
            role="student",
            group_id=group.id,
        )
        other_student = await _account(
            session,
            password_hash,
            name="Other Student",
            username="other-student",
            role="student",
            group_id=group.id,
        )
        outsider_educator = await _account(
            session,
            password_hash,
            name="Outsider Educator",
            username="outsider-educator",
            role="educator",
            group_id=other_group.id,
        )
        outsider_student = await _account(
            session,
            password_hash,
            name="Outsider Student",
            username="outsider-student",
            role="student",
            group_id=other_group.id,
        )

        course = Course(name="Demo course", group_id=group.id, created_by=admin.id)
        session.add(course)
        await session.flush()
        enrollment = CourseEnrollment(user_id=student.id, course_id=course.id)
        grant = CourseEditGrant(user_id=educator.id, course_id=course.id)
        module = Module(name="Demo module", course_id=course.id, position=1)
        session.add_all([enrollment, grant, module])
        await session.flush()
        await session.commit()

        return World(
            super_user=super_user,
            admin=admin,
            other_admin=other_admin,
            educator=educator,
            other_educator=other_educator,
            student=student,
            other_student=other_student,
            outsider_educator=outsider_educator,
            outsider_student=outsider_student,
            group_id=group.id,
            other_group_id=other_group.id,
            course_id=course.id,
            module_id=module.id,
            enrollment_id=enrollment.id,
            edit_grant_id=grant.id,
        )


@pytest_asyncio.fixture
async def super_cookies(client, world):
    return await login(client, world.super_user.username)


@pytest_asyncio.fixture
async def admin_cookies(client, world):
    return await login(client, world.admin.username)


@pytest_asyncio.fixture
async def other_admin_cookies(client, world):
    return await login(client, world.other_admin.username)


@pytest_asyncio.fixture
async def educator_cookies(client, world):
    return await login(client, world.educator.username)


@pytest_asyncio.fixture
async def other_educator_cookies(client, world):
    return await login(client, world.other_educator.username)


@pytest_asyncio.fixture
async def student_cookies(client, world):
    return await login(client, world.student.username)


@pytest_asyncio.fixture
async def other_student_cookies(client, world):
    return await login(client, world.other_student.username)


@pytest_asyncio.fixture
async def outsider_educator_cookies(client, world):
    return await login(client, world.outsider_educator.username)


@pytest_asyncio.fixture
async def outsider_student_cookies(client, world):
    return await login(client, world.outsider_student.username)
