from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class SessionOut(BaseModel):
    ok: bool
    user: UserOut


class OwnerPasswordResetRequest(BaseModel):
    setup_key: str
    new_password: str