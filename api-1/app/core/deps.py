"""FastAPI dependencies shared by the routers."""
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import decode_token
from app.db.models import User
from app.db.postgres import AsyncSessionLocal


@dataclass(frozen=True)
class CurrentUser:
    id: str  # str(users.id) - this is the only user_id ever passed to agents and tools
    email: str


async def get_db():
    if not AsyncSessionLocal:
        raise HTTPException(status_code=503, detail="Database connection not configured")
    async with AsyncSessionLocal() as session:
        yield session


def _unauthorized(detail: str = "Invalid or expired token") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})


async def get_current_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Resolves the caller from the bearer token. Client-supplied user ids are never trusted."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token")
    try:
        payload = decode_token(authorization.split(" ", 1)[1].strip())
    except jwt.PyJWTError:
        raise _unauthorized()
    email = payload.get("sub")
    if not email:
        raise _unauthorized()
    user = (await db.execute(select(User).where(User.email == email))).scalars().first()
    if user is None:
        raise _unauthorized("User no longer exists")
    return CurrentUser(id=str(user.id), email=user.email)
