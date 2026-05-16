from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    passwordConfirm: str
    university: str


class UserResponse(BaseModel):
    id: str
    email: str
    university: str
    provider: str
    createdAt: str


class AuthResponse(BaseModel):
    user: UserResponse
    token: str
