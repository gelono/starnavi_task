import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from posts.models import Post
from rest_framework_simplejwt.tokens import AccessToken


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_with_jwt(db):
    user = User.objects.create_user(username='testuser', email='test@email.com', password='testpass')
    token = AccessToken.for_user(user)
    return user, str(token)


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(username='admin', password='adminpass')


@pytest.fixture
def post(db, user_with_jwt):
    user, _ = user_with_jwt
    return Post.objects.create(author=user, title='This is title', content='This is text')
