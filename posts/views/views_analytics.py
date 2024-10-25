from django.db import models
from django.db.models import Count
from django.utils.dateparse import parse_date
from datetime import timedelta
from ninja import Router
from ninja.responses import Response

from posts.models import Comment

router = Router()


def validate_dates(date_from, date_to):
    """Validate date parameters."""
    start_date = parse_date(date_from)
    end_date = parse_date(date_to)

    if not start_date or not end_date:
        return None, None, Response({"error": "Invalid date format."}, status=400)

    if start_date > end_date:
        return None, None, Response({"error": "date_from must be earlier than date_to."}, status=400)

    return start_date, end_date, None


def get_date_range(start_date, end_date):
    """Generate a list of dates from start_date to end_date."""
    return [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]


def get_comments_data(start_date, end_date):
    """Retrieve aggregated comments data for the specified date range."""
    return (
        Comment.objects.filter(created_at__date__range=(start_date, end_date))
        .values("created_at__date")
        .annotate(
            total_comments=Count("id"),
            blocked_comments=Count("id", filter=models.Q(is_blocked=True))
        )
        .order_by("created_at__date")
    )


def build_analytics_dict(date_range, comments_data):
    """Build a dictionary to store the analytics data."""
    analytics = {date.strftime("%Y-%m-%d"): {"total_comments": 0, "blocked_comments": 0} for date in date_range}

    for entry in comments_data:
        date = entry["created_at__date"].strftime("%Y-%m-%d")
        analytics[date]["total_comments"] = entry["total_comments"]
        analytics[date]["blocked_comments"] = entry["blocked_comments"]

    return analytics


@router.get("/comments-daily-breakdown")
def comments_daily_breakdown(request):
    """
    Retrieve a daily breakdown of comments within a specified date range.

    Args:
        request: The HTTP request object.

    Returns:
        Response: A JSON response containing aggregated comment data
        for each day in the specified date range.

    Raises:
        ValidationError: If the provided date range is invalid.

    This method accepts two query parameters, `date_from` and `date_to`,
    representing the start and end dates for the analysis. It validates these
    dates and retrieves comments created within the specified range. The
    method then aggregates the comment data and returns a structured
    JSON response with daily statistics.
    """
    # Get the dates
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    # Validation
    start_date, end_date, error_response = validate_dates(date_from, date_to)
    if error_response:
        return error_response

    # Range date create
    date_range = get_date_range(start_date, end_date)

    # Get aggregated data
    comments_data = get_comments_data(start_date, end_date)

    # Create analytics
    analytics = build_analytics_dict(date_range, comments_data)

    return Response(analytics)
