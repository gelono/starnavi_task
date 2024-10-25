from ninja import Schema
from pydantic import Field, EmailStr


class RegisterSchema(Schema):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginSchema(Schema):
    username: str
    password: str
