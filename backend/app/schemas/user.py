"""
User Pydantic schemas for API requests and responses.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID


# Request schemas
class UserRegister(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    age: Optional[int] = Field(None, ge=13, le=120)


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    """Token refresh request schema."""
    refresh_token: str


class UserUpdate(BaseModel):
    """User profile update request schema."""
    full_name: Optional[str] = Field(None, max_length=255)
    age: Optional[int] = Field(None, ge=13, le=120)


# Response schemas
class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: Optional[str]
    age: Optional[int]
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserProfile(BaseModel):
    """Extended user profile response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: Optional[str]
    age: Optional[int]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[str] = None
