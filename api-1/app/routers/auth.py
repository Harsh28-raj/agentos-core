from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import CurrentUser, get_current_user, get_db
from app.core.security import MAX_PASSWORD_BYTES, create_access_token, get_password_hash, verify_password
from app.db.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

MIN_PASSWORD_LENGTH = 8


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(AuthRequest):
    @field_validator("password")
    @classmethod
    def password_policy(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes")
        return value


def _normalize(email: str) -> str:
    return email.strip().lower()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = _normalize(request.email)
    existing = (await db.execute(select(User).where(func.lower(User.email) == email))).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(email=email, hashed_password=get_password_hash(request.password))
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        # Two concurrent registrations for the same email
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    await db.refresh(new_user)
    return {"message": "User created successfully", "user": {"id": str(new_user.id), "email": new_user.email}}


@router.post("/login")
async def login(request: AuthRequest, db: AsyncSession = Depends(get_db)):
    email = _normalize(request.email)
    user = (await db.execute(select(User).where(func.lower(User.email) == email))).scalars().first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": user.email, "id": str(user.id)}}


@router.get("/me")
async def get_me(user: CurrentUser = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}
