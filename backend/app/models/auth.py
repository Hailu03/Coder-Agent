from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=50)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    avatar: Optional[str] = None

class UserResponse(UserBase):
    id: int
    avatar: Optional[str] = None
    is_active: bool = True

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    refresh_token: str  # Added refresh token
    token_type: str
    user: UserResponse

class TokenPayload(BaseModel):
    sub: str
    exp: int
    token_type: str  # 'access' or 'refresh'

class RefreshToken(BaseModel):
    refresh_token: str

class LoginRequest(BaseModel):
    username: str
    password: str