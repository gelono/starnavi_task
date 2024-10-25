from ninja import Router
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from ninja.responses import Response

from posts.ai_tools import moderate_content_with_ai
from posts.models import Post
from posts.schemas import PostInSchema, PostOutSchema
from typing import List

router = Router()

# CRUD for Posts

@router.post("/create/", response={201: PostOutSchema}, url_name="create_post")
def create_post(request, payload: PostInSchema):
    """
    Create a new post.

    Args:
        request: The HTTP request object.
        payload (PostInSchema): The data required to create a post, including title and content.

    Returns:
        PostOutSchema: The created post details.

    Raises:
        HttpError: If authentication is required or if inappropriate content is detected.

    This method performs the following actions:
        - Checks if the user is authenticated.
        - Validates the title and content for inappropriate content using AI moderation.
        - Creates a new post with the provided data.
        - If the content is deemed inappropriate, it returns a 403 response with a relevant message.
    """
    user = request.user

    if not user.is_authenticated:
        raise HttpError(401, "Authentication required")

    result, reason = moderate_content_with_ai(payload.title)
    if not result:
        result, reason = moderate_content_with_ai(payload.content)

    post = Post.objects.create(
        author=user,
        is_blocked=result,
        block_reason=reason,
        **payload.dict()
    )

    if post.is_blocked:
        return Response(
            {"detail": f"Post was blocked, reason - it contains inappropriate content: {post.block_reason}"},
            status=400
        )

    return Response(PostOutSchema.from_orm(post), status=201)



@router.get("/posts/", response=List[PostOutSchema])
def list_posts(request):
    """
    Retrieve a list of all posts.

    Args:
        request: The HTTP request object.

    Returns:
        List[PostOutSchema]: A list of posts that are not blocked, with their details.

    This method fetches all posts from the database, filtering out any posts that are marked as blocked.
    The response contains the details of each post, including title, content, creation date,
    last updated date, and the author's username.
    """
    posts = Post.objects.filter(is_blocked=False)
    post_list = [PostOutSchema.from_orm(post) for post in posts]

    return Response(post_list)


@router.get("/{post_id}/", response=PostOutSchema)
def get_post(request, post_id: int):
    """
    Retrieve a specific post by its ID.

    Args:
        request: The HTTP request object.
        post_id (int): The ID of the post to retrieve.

    Returns:
        PostOutSchema: The details of the requested post, including title, content,
        creation date, last updated date, and the author's username.

    This method fetches a post from the database using the provided post ID.
    If the post does not exist, a 404 Not Found error is raised.
    """
    post = get_object_or_404(Post, id=post_id)

    return Response(PostOutSchema.from_orm(post), status=200)


@router.put("/{post_id}/", response=PostOutSchema)
def update_post(request, post_id: int, payload: PostInSchema):
    """
    Update an existing post by its ID.

    Args:
        request: The HTTP request object.
        post_id (int): The ID of the post to update.
        payload (PostInSchema): The data to update the post with, which may include
        optional fields for title and content.

    Returns:
        PostOutSchema: The updated post details, including title, content,
        creation date, last updated date, and the author's username.

    Raises:
        HttpError: If the user is not authorized to edit the post
        (if they are not the author or not a staff member).

    This method retrieves a post from the database using the provided post ID and
    updates its fields based on the provided payload. Only the post's author or
    an admin can make updates. If the post is not found, a 404 Not Found error is raised.
    """
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user and not request.user.is_staff:
        raise HttpError(403, "You are not allowed to edit this post.")

    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(post, attr, value)

    post.save()

    if post.is_blocked:
        return Response(
            {"detail": f"Post was blocked, reason - it contains inappropriate content: {post.block_reason}"},
            status=400
        )

    return Response(PostOutSchema.from_orm(post), status=200)


@router.delete("/{post_id}/")
def delete_post(request, post_id: int):
    """
    Delete a post by its ID.

    Args:
        request: The HTTP request object.
        post_id (int): The ID of the post to delete.

    Returns:
        dict: A response indicating the success of the deletion.

    Raises:
        HttpError: If the user is not authorized to delete the post
        (if they are not the author or not a staff member).

    This method retrieves a post from the database using the provided post ID
    and deletes it. Only the post's author or an admin can perform the deletion.
    If the post is not found, a 404 Not Found error is raised.
    """
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user and not request.user.is_staff:
        raise HttpError(403, "You are not allowed to delete this post.")

    post.delete()

    return Response({"success": True}, status=200)
