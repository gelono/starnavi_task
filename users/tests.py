import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAuthAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_register_user_success(self):
        url = reverse("api-1.0.0:register")
        payload = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password": "TestPassword123"
        }
        response = self.client.post(url, payload, format="json")

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"message": "User registered successfully"}
        assert User.objects.filter(email=payload["email"]).exists()

    def test_register_user_email_exists(self):
        existing_user = User.objects.create_user(
            username="existing_user",
            email="existing_user@example.com",
            password="TestPassword123"
        )
        url = reverse("api-1.0.0:register")
        payload = {
            "username": "new_user",
            "email": existing_user.email,
            "password": "TestPassword123"
        }
        response = self.client.post(url, payload, format="json")

        # Assertions
        assert response.status_code == 400
        assert response.json() == {"detail": "Email already exists"}

    def test_login_user_success(self):
        # Create user
        user = User.objects.create_user(
            username="test_user",
            password="TestPassword123"
        )
        url = reverse("api-1.0.0:login")
        payload = {
            "username": user.username,
            "password": "TestPassword123"
        }
        response = self.client.post(url, payload, format="json")

        # Assertions
        assert response.status_code == 200
        assert "access" in response.json()
        assert "refresh" in response.json()

    def test_login_user_invalid_credentials(self):
        url = reverse("api-1.0.0:login")
        payload = {
            "username": "non_existing_user",
            "password": "WrongPassword"
        }
        response = self.client.post(url, payload, format="json")

        # Assertions
        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid credentials"}
