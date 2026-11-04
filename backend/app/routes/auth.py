from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.passwords import verify_password
from app.schemas.user import LoginRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

INVALID_LOGIN = "Invalid username or password"


@router.post("/login", response_model=UserRead)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_LOGIN
        )
    request.session["user_id"] = user.id
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request):
    request.session.clear()


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
