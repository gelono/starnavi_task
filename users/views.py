from ninja import Router
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from ninja.errors import HttpError
from rest_framework_simplejwt.tokens import RefreshToken
from users.schemas import RegisterSchema, LoginSchema

router = Router()


@router.post("/register")
def register(request, payload: RegisterSchema):
    if User.objects.filter(email=payload.email).exists():
        raise HttpError(400, "Email already exists")
    User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password
    )
    return {"message": "User registered successfully"}


@router.post("/login")
def login(request, payload: LoginSchema):
    user = authenticate(username=payload.username, password=payload.password)
    if user is None:
        raise HttpError(400, "Invalid credentials")

    # Generation JWT-tokens
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
