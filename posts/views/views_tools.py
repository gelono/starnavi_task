from django.core.exceptions import PermissionDenied

from posts.models import Post, Comment
from posts.tasks import send_auto_reply
from django.shortcuts import get_object_or_404


def check_post_blocked(post: Post):
    if post.is_blocked:
        raise PermissionDenied("You cannot create a comment for blocked content.")


def check_parent_comment_blocked(parent_id: int):
    parent_comment = get_object_or_404(Comment, id=parent_id)
    if parent_comment.is_blocked:
        raise PermissionDenied("You cannot create a comment for blocked content.")


def schedule_auto_reply_if_enabled(post: Post, comment: Comment):
    if post.auto_reply_enabled and not comment.is_blocked:
        send_auto_reply.apply_async(
            args=[post.id, comment.id],
            countdown=post.reply_delay * 60
        )
