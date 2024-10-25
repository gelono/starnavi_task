from django.db.models.signals import pre_save
from django.dispatch import receiver

from .ai_tools import moderate_content_with_ai
from .models import Comment, Post


@receiver(pre_save, sender=Comment)
def check_comment_content(sender, instance, **kwargs):
    """
    Pre-save signal handler to check the content of a comment for inappropriate material.

    This method is triggered before a comment is saved to the database. It uses an AI-based
    moderation tool to analyze the comment's content. If inappropriate content is detected,
    the comment is marked as blocked by setting the `is_blocked` field to True, and the
    `block_reason` field is populated with the reason for the block.

    Args:
        sender: The model class (Comment) that sent the signal.
        instance: The instance of the Comment model that is being saved.
        **kwargs: Additional keyword arguments.

    Returns:
        None: The method modifies the `instance` directly by updating its fields if inappropriate
              content is detected.
    """
    result, reason = moderate_content_with_ai(instance.content)
    if result:
        instance.is_blocked = True
        instance.block_reason = reason


@receiver(pre_save, sender=Post)
def check_post_content(sender, instance, **kwargs):
    """
    Pre-save signal handler to check both the title and content of a post for inappropriate material.

    This method is triggered before a post is saved to the database. It uses an AI-based moderation tool
    to analyze the post's title and content. If either contains inappropriate material, the post is marked
    as blocked by setting the `is_blocked` field to True, and the `block_reason` field is updated with
    the reason for blocking. The post is saved regardless of content moderation results, but marked
    as blocked if necessary.

    Args:
        sender: The model class (Post) that sent the signal.
        instance: The instance of the Post model that is being saved.
        **kwargs: Additional keyword arguments.

    Returns:
        None: The method modifies the `instance` directly by updating its fields if inappropriate
              content or title is detected.
    """
    if instance.title:
        result, reason = moderate_content_with_ai(instance.title)
        if result:
            instance.is_blocked = True
            instance.block_reason = reason

    if hasattr(instance, 'content'):
        result, reason = moderate_content_with_ai(instance.content)
        if result:
            instance.is_blocked = True
            instance.block_reason = reason
