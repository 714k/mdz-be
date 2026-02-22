"""
Authentication request/response schemas.
"""

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token data."""

    user_id: int | None = None


class UserResponse(BaseModel):
    """User profile response."""

    id: int
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
