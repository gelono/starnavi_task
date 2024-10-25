import random
import time
import pytest
from django.urls import reverse
from posts.models import Comment
from posts.tests.tools import safety_categories, storage, pause


class TestCommentAPI:
    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_with_jwt, post):
        self.api_client = api_client
        self.user, self.token = user_with_jwt
        self.post = post
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.safety_categories = safety_categories
        self.storage = storage
        self.pause = pause  # It needs to pause between requests to AI-service doesn't ban your IP

    @pytest.mark.django_db
    def test_create_comment(self):
        payload = {
            "content": "This is a comment.",
            "parent_id": None
        }

        url = reverse('api-1.0.0:create_comment', args=[self.post.id])
        response = self.api_client.post(url, payload, format='json')
        data = response.json()

        assert response.status_code == 201
        assert data['content'] == payload['content']
        assert data['author'] == self.user.username

    @pytest.mark.django_db
    def test_list_comments(self):
        # Comment create
        comment = Comment.objects.create(author=self.user, post=self.post, content="This is a comment.")

        url = reverse('api-1.0.0:list_comments', args=[self.post.id])
        response = self.api_client.get(url)
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]['content'] == comment.content

    @pytest.mark.django_db
    def test_update_comment(self):
        time.sleep(self.pause)
        # Comment create to update
        comment = Comment.objects.create(author=self.user, post=self.post, content="Old comment.")

        payload = {
            "content": "Updated comment"
        }

        url = reverse('api-1.0.0:update_comment', args=[comment.id])
        response = self.api_client.put(url, payload, format='json')
        data = response.json()

        assert response.status_code == 200
        assert data['content'] == payload['content']

    @pytest.mark.django_db
    def test_delete_comment(self):
        # Comment create to delete
        comment = Comment.objects.create(author=self.user, post=self.post, content="This comment will be deleted.")

        url = reverse('api-1.0.0:delete_comment', args=[comment.id])
        response = self.api_client.delete(url)
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert not Comment.objects.filter(id=comment.id).exists()

    @pytest.mark.django_db
    def test_create_blocked_comment(self):
        time.sleep(self.pause)
        # Blocked comment create
        payload = {
            "content": f"{random.choice(self.storage)}",
        }

        url = reverse('api-1.0.0:create_comment', args=[self.post.id])
        response = self.api_client.post(url, payload, format='json')
        data = response.json()

        assert response.status_code == 400
        assert any(reason in data['detail'] for reason in self.safety_categories), \
            f"Expected one of {self.safety_categories}, but got {data['detail']}"

    @pytest.mark.django_db
    def test_create_comment_as_unauthenticated_user(self):
        payload = {
            "content": "This is a comment"
        }

        url = reverse('api-1.0.0:create_comment', args=[self.post.id])
        self.api_client.credentials()
        response = self.api_client.post(url, payload, format='json')
        data = response.json()

        assert response.status_code == 401
        assert data['detail'] == "Authentication required"

    @pytest.mark.django_db
    def test_update_comment_as_unauthenticated_user(self):
        # Comment create to update
        comment = Comment.objects.create(author=self.user, post=self.post, content="Old comment.")

        payload = {
            "content": "Updated comment"
        }

        url = reverse('api-1.0.0:update_comment', args=[comment.id])
        self.api_client.credentials()
        response = self.api_client.put(url, payload, format='json')
        data = response.json()

        assert response.status_code == 403
        assert data['detail'] == "You are not allowed to edit this comment."

    @pytest.mark.django_db
    def test_create_comment_to_blocked_post(self):
        # Post blocking
        self.post.is_blocked = True
        self.post.save()

        payload = {
            "content": "This is a comment.",
            "parent_id": None
        }

        url = reverse('api-1.0.0:create_comment', args=[self.post.id])
        response = self.api_client.post(url, payload, format='json')

        # Post unblocking
        self.post.is_blocked = False
        self.post.save()

        data = response.json()

        assert response.status_code == 403
        assert data['detail'] == "You cannot create a comment for blocked content."

    @pytest.mark.django_db
    def test_update_blocked_comment(self):
        time.sleep(self.pause)
        # Comment create to update
        comment = Comment.objects.create(author=self.user, post=self.post, content="Old comment.")

        payload = {
            "content": f"{random.choice(self.storage)}",
        }

        url = reverse('api-1.0.0:update_comment', args=[comment.id])
        response = self.api_client.put(url, payload, format='json')
        data = response.json()

        assert response.status_code == 400
        assert any(reason in data['detail'] for reason in self.safety_categories), \
            f"Expected one of {self.safety_categories}, but got {data['detail']}"
