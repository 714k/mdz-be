"""
Authentication endpoints with Redis integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from app.core.logging import logger
from app.core.monitoring import auth_attempts_total
from app.core.cache import cache  # <-- Redis

router = APIRouter(prefix="/auth", tags=["authentication"])


# -----------------------------
# REGISTER
# -----------------------------
@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""

    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        auth_attempts_total.labels(status="failed_duplicate").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    hashed_password = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    auth_attempts_total.labels(status="registered").inc()
    logger.info("user_registered", user_id=new_user.id, email=new_user.email)

    # Store registration event in Redis
    await cache.set(
        f"auth:registered:{new_user.id}", {"email": new_user.email}, expire=3600
    )

    return new_user


# -----------------------------
# LOGIN
# -----------------------------
@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and receive JWT access token."""

    user = db.query(User).filter(User.email == credentials.email).first()

    # Track login attempts in Redis
    await cache.set(
        f"auth:login_attempt:{credentials.email}", {"attempt": "login"}, expire=300
    )

    if not user or not verify_password(credentials.password, user.hashed_password):
        auth_attempts_total.labels(status="failed_invalid").inc()

        # Increment failed attempts counter
        key = f"auth:failed:{credentials.email}"
        failed = await cache.get(key) or 0
        await cache.set(key, int(failed) + 1, expire=600)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        auth_attempts_total.labels(status="failed_inactive").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Store session in Redis
    await cache.set(
        f"auth:session:{user.id}",
        {"email": user.email, "token": access_token},
        expire=3600,
    )

    auth_attempts_total.labels(status="success").inc()
    logger.info("user_logged_in", user_id=user.id, email=user.email)

    return {"access_token": access_token, "token_type": "bearer"}
