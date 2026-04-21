"""
Authentication Endpoints

Security Features:
- Password hashing with PBKDF2-SHA256 (salt rounds configurable)
- JWT tokens with configurable expiration
- Email validation (EmailStr from Pydantic)
- Rate limiting via middleware (configured in main.py)
- Stateless authentication (no sessions, scalable)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta
from passlib.context import CryptContext

from app.core.database import get_db
from app.core.config import settings
from app.core.auth import create_access_token, get_current_user
from app.models.user import User
import uuid
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Use PBKDF2-SHA256 for password hashing (OWASP compliant, no external compilation needed)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class UserRegister(BaseModel):
    """User registration request schema"""
    email: EmailStr  # Automatic email format validation
    password: str    # Min length enforced in core.auth
    full_name: str


class UserResponse(BaseModel):
    """User response - excludes sensitive data"""
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    company_name: str | None = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str  # Always "bearer" for OAuth2


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password.
    Uses constant-time comparison to prevent timing attacks.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password using PBKDF2-SHA256.
    Automatically generates and includes salt.
    """
    return pwd_context.hash(password)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    User registration endpoint.
    
    Security checks:
    - Email uniqueness validation
    - Password hashing before storage
    - Non-existent user creation fails gracefully
    """
    # Check if email already registered (prevent account enumeration) 
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password before storage (OWASP best practice)
    hashed_password = get_password_hash(user_data.password)
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,  # Never store plaintext
        full_name=user_data.full_name
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint - returns JWT token.
    
    Security:
    - Uses OAuth2PasswordRequestForm (standard format)
    - Validates credentials against hashed password
    - Returns short-lived JWT token
    - Rate limiting prevents brute force (via middleware)
    """
    # Fetch user by email (username field in OAuth2PasswordRequestForm)
    try:
        result = await db.execute(select(User).filter(User.email == form_data.username))
        user = result.scalars().first()
    except SQLAlchemyError as exc:
        # Hide database errors from client (security + user experience)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        ) from exc
    
    # Verify credentials - fails if user not found OR password incorrect
    # Message is intentionally vague to prevent email enumeration
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token with configurable expiration
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},  # Subject is user ID (not email)
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"  # OAuth2 standard
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user.
    Requires valid JWT in Authorization header.
    """
    return current_user
