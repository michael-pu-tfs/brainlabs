from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None
    is_google_account: bool = False

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_google_account: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str 