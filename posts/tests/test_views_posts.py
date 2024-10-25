import time
import random

import pytest
from django.urls import reverse
from posts.models import Post
from posts.tests.tools import safety_categories, storage, pause


class TestPostsAPI:
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_with_jwt):
        self.api_client = api_client
        self.user, self.token = user_with_jwt
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.safety_categories = safety_categories
        self.storage = storage
        self.pause = pause  # It needs to pause between requests to AI-service doesn't ban your IP

    @pytest.mark.django_db
    def test_create_post(self):
        # Define the payload for creating a post
        payload = {
            "title": "New Post",
            "content": "This is a new post content."
        }

        # Make POST request to create a post
        url = reverse('api-1.0.0:create_post')
        response = self.api_client.post(url, payload, format='json')
        data = response.json()

        # Assertions
        assert response.status_code == 201
        assert data['title'] == "New Post"
        assert data['content'] == "This is a new post content."

    @pytest.mark.django_db
    def test_list_posts(self, post):
        time.sleep(self.pause)
        # Make request
        url = reverse('api-1.0.0:list_posts')
        response = self.api_client.get(url)
        data = response.json()

        # Assertions
        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]['title'] == post.title

    @pytest.mark.django_db
    def test_get_post(self, post):
        url = reverse('api-1.0.0:get_post', args=[post.id])
        response = self.api_client.get(url)
        data = response.json()

        # Assertions
        assert response.status_code == 200
        assert data['title'] == post.title
        assert data['content'] == post.content

    @pytest.mark.django_db
    def test_update_post(self, post):
        time.sleep(self.pause)
        # Define the payload for updating a post
        payload = {
            "title": "Update Title",
            "content": "Updated"
        }

        # Make request
        url = reverse('api-1.0.0:update_post', args=[post.id])
        response = self.api_client.put(url, payload, format='json')
        data = response.json()

        # Assertions
        assert response.status_code == 200
        assert data['title'] == "Update Title"
        assert data['content'] == "Updated"

    @pytest.mark.django_db
    def test_update_blocked_post(self, post):
        time.sleep(self.pause)
        # Define the payload for creating a blocked post
        blocked_payload = {
            "title": f"{random.choice(self.storage)}",
            "content": "This content is not allowed because title contains bad language."
        }

        # Make PUT request to update a blocked post
        url = reverse('api-1.0.0:update_post', args=[post.id])
        response = self.api_client.put(url, blocked_payload, format='json')
        data = response.json()

        # Assertions
        assert response.status_code == 400
        assert any(reason in data['detail'] for reason in self.safety_categories), \
            f"Expected one of {self.safety_categories}, but got {data['detail']}"

    @pytest.mark.django_db
    def test_delete_post(self, post):
        # Make DELETE request to delete the post
        url = reverse('api-1.0.0:delete_post', args=[post.id])
        response = self.api_client.delete(url)
        data = response.json()

        # Assertions
        assert response.status_code == 200
        assert data['success'] is True

        # Check if post is actually deleted
        assert not Post.objects.filter(id=post.id).exists()

    @pytest.mark.django_db
    def test_create_blocked_post(self):
        time.sleep(self.pause)
        # Define the payload for creating a blocked post
        blocked_payload = {
            "title": "Just title",
            "content": f"{random.choice(self.storage)}"
        }

        # Make POST request to create a blocked post
        url = reverse('api-1.0.0:create_post')
        response = self.api_client.post(url, blocked_payload, format='json')
        data = response.json()

        # Assertions
        assert response.status_code == 400
        assert any(reason in data['detail'] for reason in self.safety_categories), \
            f"Expected one of {self.safety_categories}, but got {data['detail']}"

    @pytest.mark.django_db
    def test_create_post_as_unauthenticated_user(self):
        payload = {
            "title": "New Post",
            "content": "This is the content of the new post."
        }

        url = reverse('api-1.0.0:create_post')
        self.api_client.credentials()
        response = self.api_client.post(url, payload, format='json')
        data = response.json()

        assert response.status_code == 401
        assert data['detail'] == "Authentication required"

    @pytest.mark.django_db
    def test_update_post_as_unauthenticated_user(self, post):
        # Define the payload for updating a post
        payload = {
            "title": "Update Title",
            "content": "Updated"
        }

        # Make request
        url = reverse('api-1.0.0:update_post', args=[post.id])
        self.api_client.credentials()
        response = self.api_client.put(url, payload, format='json')
        data = response.json()

        # Assertions
        assert response.status_code == 403
        assert data['detail'] == "You are not allowed to edit this post."
