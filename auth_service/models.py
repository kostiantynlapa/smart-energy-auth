"""
Pydantic models for request/response schemas.
"""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """User registration request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    allowed_storages: list[str] = Field(default_factory=list)


class RegisterResponse(BaseModel):
    """User registration response with TOTP setup."""
    qr_code_base64: str
    totp_secret: str


class LoginRequest(BaseModel):
    """User login request schema."""
    username: str
    password: str
    totp_code: str


class TokenResponse(BaseModel):
    """Successful login response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str  # username
    role: str = "user"  # "user" or "admin"
    allowed_storages: list[str] = Field(default_factory=list)
    exp: int  # expiration timestamp


class AdminUserList(BaseModel):
    """Admin user list response schema."""
    username: str
    role: str
    allowed_storages: list[str]


class AdminUserCreate(BaseModel):
    """Admin create user request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: str = Field(default="user")
    allowed_storages: list[str] = Field(default_factory=list)


class AdminStorageUpdate(BaseModel):
    """Admin update storages request schema."""
    allowed_storages: list[str]


class AdminRoleUpdate(BaseModel):
    """Admin update role request schema."""
    role: str
