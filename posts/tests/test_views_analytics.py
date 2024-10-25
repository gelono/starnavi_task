from datetime import datetime
import json
import pytest
from django.utils import timezone
from posts.models import Comment
from posts.views.views_analytics import validate_dates, get_date_range, get_comments_data, build_analytics_dict


class TestValidateDates:

    def process_error_response(self, response):
        if response.status_code >= 400:
            # Decoding the response body from bytes
            response_body = response._container[0].decode('utf-8')

            # Converting response body to JSON
            error_data = json.loads(response_body)
            return error_data.get("error", "Unknown error")

        return None

    def test_validate_dates_valid(self):
        date_from = "2024-10-01"
        date_to = "2024-10-10"
        start_date, end_date, error_response = validate_dates(date_from, date_to)

        assert start_date is not None
        assert end_date is not None
        assert error_response is None

    def test_validate_dates_invalid_format(self):
        date_from = "invalid-date"
        date_to = "2024-10-10"
        start_date, end_date, error_response = validate_dates(date_from, date_to)
        error = self.process_error_response(error_response)

        assert start_date is None
        assert end_date is None
        assert error_response.status_code == 400
        assert "Invalid date format" in error

    def test_validate_dates_from_later_than_to(self):
        date_from = "2024-10-10"
        date_to = "2024-10-01"
        start_date, end_date, error_response = validate_dates(date_from, date_to)
        error = self.process_error_response(error_response)

        assert start_date is None
        assert end_date is None
        assert error_response.status_code == 400
        assert "date_from must be earlier than date_to" in error


class TestGetDateRange:

    def test_get_date_range(self):
        start_date = datetime(2024, 10, 1)
        end_date = datetime(2024, 10, 3)
        date_range = get_date_range(start_date, end_date)

        assert len(date_range) == 3
        assert date_range[0] == start_date
        assert date_range[-1] == end_date


@pytest.mark.django_db
class TestGetCommentsData:
    @pytest.fixture(autouse=True)
    def setup(self, user_with_jwt, post):
        self.user, self.token = user_with_jwt
        self.post = post

    def test_get_comments_data(self):
        # Create test comments with different dates and statuses
        comment_1 = Comment.objects.create(author=self.user, post=self.post, content="Test comment 1", is_blocked=False)
        comment_1.created_at = timezone.make_aware(datetime(2024, 1, 1))
        comment_1.save()

        comment_2 = Comment.objects.create(author=self.user, post=self.post, content="Test comment 2", is_blocked=True)
        comment_2.created_at = timezone.make_aware(datetime(2024, 1, 2))
        comment_2.save()

        comment_3 = Comment.objects.create(author=self.user, post=self.post, content="Test comment 3", is_blocked=False)
        comment_3.created_at = timezone.make_aware(datetime(2024, 1, 3))
        comment_3.save()

        # Create date range
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)
        data = get_comments_data(start_date, end_date)

        # Assertions
        assert len(data) == 3

        for entry in data:
            date = entry["created_at__date"]
            if date == datetime(2024, 1, 1).date():
                assert entry["total_comments"] == 1
                assert entry["blocked_comments"] == 0
            elif date == datetime(2024, 1, 2).date():
                assert entry["total_comments"] == 1
                assert entry["blocked_comments"] == 1
            elif date == datetime(2024, 1, 3).date():
                assert entry["total_comments"] == 1
                assert entry["blocked_comments"] == 0


class TestBuildAnalyticsDict:

    def test_build_analytics_dict(self):
        date_range = [datetime(2024, 10, 1), datetime(2024, 10, 2)]
        comments_data = [
            {"created_at__date": datetime(2024, 10, 1), "total_comments": 5, "blocked_comments": 2},
            {"created_at__date": datetime(2024, 10, 2), "total_comments": 3, "blocked_comments": 1}
        ]
        analytics = build_analytics_dict(date_range, comments_data)
        assert analytics["2024-10-01"]["total_comments"] == 5
        assert analytics["2024-10-01"]["blocked_comments"] == 2
        assert analytics["2024-10-02"]["total_comments"] == 3
        assert analytics["2024-10-02"]["blocked_comments"] == 1


@pytest.mark.django_db
class TestCommentsDailyBreakdown:

    def test_comments_daily_breakdown_valid(self, client):
        url = "/api/posts/analytics/comments-daily-breakdown?date_from=2024-10-01&date_to=2024-10-10"
        response = client.get(url)
        assert response.status_code == 200
        assert "2024-10-01" in response.json()

    def test_comments_daily_breakdown_invalid_date_range(self, client):
        url = "/api/posts/analytics/comments-daily-breakdown?date_from=invalid-date&date_to=2024-10-10"
        response = client.get(url)
        assert response.status_code == 400
        assert "Invalid date format" in response.json()["error"]

    def test_comments_daily_breakdown_invalid_range(self, client):
        url = "/api/posts/analytics/comments-daily-breakdown?date_from=2024-10-10&date_to=2024-10-01"
        response = client.get(url)
        assert response.status_code == 400
        assert "date_from must be earlier than date_to" in response.json()["error"]
