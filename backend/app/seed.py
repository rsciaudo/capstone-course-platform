from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Group, User
from app.passwords import hash_password

# Local accounts for trying each role. Shared password: password
SEED_PASSWORD = "password"
SEED_GROUP_NAME = "Demo group"

UNGROUPED = (
    {"username": "super", "name": "Super User", "role": "super-user"},
    {"username": "admin", "name": "Admin", "role": "admin"},
)
GROUPED = (
    {"username": "educator", "name": "Educator", "role": "educator"},
    {"username": "student", "name": "Student", "role": "student"},
)


async def seed_users(session: AsyncSession) -> None:
    usernames = [user["username"] for user in (*UNGROUPED, *GROUPED)]
    result = await session.execute(select(User).where(User.username.in_(usernames)))
    existing = {user.username: user for user in result.scalars()}
    if len(existing) == len(usernames):
        return

    password_hash = hash_password(SEED_PASSWORD)
    for spec in UNGROUPED:
        if spec["username"] in existing:
            continue
        user = User(
            name=spec["name"],
            username=spec["username"],
            password_hash=password_hash,
            role=spec["role"],
            group_id=None,
        )
        session.add(user)
        await session.flush()
        existing[spec["username"]] = user

    missing_grouped = [spec for spec in GROUPED if spec["username"] not in existing]
    if missing_grouped:
        group = await _seed_group(session, existing)
        for spec in missing_grouped:
            session.add(
                User(
                    name=spec["name"],
                    username=spec["username"],
                    password_hash=password_hash,
                    role=spec["role"],
                    group_id=group.id,
                )
            )

    await session.commit()


async def _seed_group(session: AsyncSession, existing: dict[str, User]) -> Group:
    for username in ("educator", "student"):
        user = existing.get(username)
        if user is not None and user.group_id is not None:
            group = await session.get(Group, user.group_id)
            if group is not None:
                return group

    result = await session.execute(
        select(Group).where(Group.name == SEED_GROUP_NAME).order_by(Group.id)
    )
    group = result.scalars().first()
    if group is not None:
        return group

    group = Group(name=SEED_GROUP_NAME, created_by=existing["admin"].id)
    session.add(group)
    await session.flush()
    return group
