from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.postgres import AsyncSessionLocal
from app.db.models import User
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

class AuthRequest(BaseModel):
    email: EmailStr
    password: str

async def get_db():
    if not AsyncSessionLocal:
        raise HTTPException(status_code=500, detail="Database connection not initialized")
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/register")
async def register(request: AuthRequest, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(request.password)
    new_user = User(email=request.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {"message": "User created successfully", "user": {"id": new_user.id, "email": new_user.email}}

@router.post("/login")
async def login(request: AuthRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": {"email": user.email, "id": user.id}}
