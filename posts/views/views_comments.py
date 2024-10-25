from django.core.exceptions import PermissionDenied
from ninja import Router
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from ninja.responses import Response

from posts.models import Post, Comment
from posts.schemas import CommentInSchema, CommentOutSchema
from typing import List
from posts.views.views_tools import check_post_blocked, check_parent_comment_blocked, schedule_auto_reply_if_enabled

router = Router()

# CRUD for Comments

@router.post("/{post_id}/create/", response=CommentOutSchema)
def create_comment(request, post_id: int, payload: CommentInSchema):
    """
    Handle the creation of a comment for a specific post.

    This function creates a comment associated with a given post. It first verifies if the
    post or the parent comment (if any) is blocked, and if so, prevents further action.

    The content of the comment is analyzed, and if inappropriate, the comment is saved but marked
    as blocked, with the reason stored in the `block_reason` field. If the post has an auto-reply
    feature enabled, a task to send an automatic reply is scheduled after the specified delay.

    If the post or parent comment is blocked, or the content is deemed inappropriate, a relevant
    error message is returned as a JSON response.

    Args:
        request: The HTTP request object containing the user details.
        post_id (int): The ID of the post to which the comment belongs.
        payload (CommentInSchema): The schema containing the comment's data, including content and
                                   optional parent comment ID.

    Returns:
        Response: A JSON response with an error message if the content or post is blocked, or
                      if inappropriate content is detected. Otherwise, returns the created comment
                      data as a `CommentOutSchema` object.

    Raises:
        PermissionDenied: If the post or parent comment is blocked, preventing further actions.
    """
    post = get_object_or_404(Post, id=post_id)

    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    try:
        # Check if the post is blocked
        check_post_blocked(post)

        # Check if the parent comment is blocked
        if payload.parent_id:
            check_parent_comment_blocked(payload.parent_id)

        # Create comment
        comment = Comment.objects.create(
            author=request.user,
            post=post,
            content=payload.content,
            parent_id=payload.parent_id
        )

        if comment.is_blocked:
            return Response(
                {"detail": f"Comment was blocked, reason - it contains inappropriate content: {comment.block_reason}"},
                status=400
            )

        # Schedule auto-reply if enabled
        schedule_auto_reply_if_enabled(post, comment)

        return Response(CommentOutSchema.from_orm(comment), status=201)

    except PermissionDenied as e:
        return Response({"detail": str(e)}, status=403)


@router.get("/{post_id}/comments/", response=List[CommentOutSchema])
def list_comments(request, post_id: int):
    """
    Retrieve a list of comments for a specific post.

    Args:
        request: The HTTP request object.
        post_id (int): The ID of the post for which to retrieve comments.

    Returns:
        List[CommentOutSchema]: A list of comments associated with the specified post,
        excluding any comments that are marked as blocked.
    """
    comments = Comment.objects.filter(post_id=post_id, is_blocked=False)
    comments_list = [CommentOutSchema.from_orm(comment) for comment in comments]

    return Response(comments_list)


@router.put("/{comment_id}/", response=CommentOutSchema)
def update_comment(request, comment_id: int, payload: CommentInSchema):
    """
    Update an existing comment.

    Args:
        request: The HTTP request object.
        comment_id (int): The ID of the comment to be updated.
        payload (CommentInSchema): The data for updating the comment, which may include new content.

    Returns:
        CommentOutSchema: The updated comment if the operation is successful.

    Raises:
        HttpError: If the user is not the author of the comment and is not an admin.

    The method checks whether the user has permission to edit the comment:
        - Only the author of the comment or an admin can update it.

    The payload fields are updated partially, allowing optional fields to be modified without requiring all fields to be provided.
    """
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user and not request.user.is_staff:
        raise HttpError(403, "You are not allowed to edit this comment.")

    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(comment, attr, value)

    comment.save()

    if comment.is_blocked:
        return Response(
            {"detail": f"Comment was blocked, reason - it contains inappropriate content: {comment.block_reason}"},
            status=400
        )

    return Response(CommentOutSchema.from_orm(comment), status=200)


@router.delete("/{comment_id}/")
def delete_comment(request, comment_id: int):
    """
    Delete an existing comment.

    Args:
        request: The HTTP request object.
        comment_id (int): The ID of the comment to be deleted.

    Returns:
        dict: A success message indicating the comment has been deleted.

    Raises:
        HttpError: If the user is not the author of the comment and is not an admin.

    The method checks whether the user has permission to delete the comment:
        - Only the author of the comment or an admin can delete it.
    """
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user and not request.user.is_staff:
        raise HttpError(403, "You are not allowed to delete this comment.")

    comment.delete()

    return Response({"success": True}, status=200)
