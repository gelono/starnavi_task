from ninja import Schema
from typing import Optional
from datetime import datetime


# Post schema for requests
class PostInSchema(Schema):
    title: str = None
    content: str = None
    auto_reply_enabled: bool = False
    reply_delay: int = 0


# Post schema for responses
class PostOutSchema(Schema):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_blocked: bool
    block_reason: str
    author: str
    auto_reply_enabled: bool
    reply_delay: int

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @staticmethod
    def from_orm(post):
        """
        Converting the output to the correct format
        :param post: Post model instance
        :return: dict
        """
        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "is_blocked": post.is_blocked,
            "block_reason": post.block_reason,
            "author": post.author.username,
            "auto_reply_enabled": post.auto_reply_enabled,
            "reply_delay": post.reply_delay
        }


# Comment schema for requests
class CommentInSchema(Schema):
    content: str = None
    parent_id: Optional[int] = None  # For replies to comments


# Comment schema for responses
class CommentOutSchema(Schema):
    id: int
    content: str
    post_id: int
    parent_id: Optional[int] = None  # For replies to comments
    created_at: datetime
    updated_at: datetime
    is_blocked: bool
    author: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @staticmethod
    def from_orm(comment):
        """
        Converting the output to the correct format
        :param comment: Comment model instance
        :return: dict
        """
        return {
            "id": comment.id,
            "content": comment.content,
            "post_id": comment.post_id,
            "parent_id": comment.parent_id if comment.parent_id else None,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "is_blocked": comment.is_blocked,
            "block_reason": comment.block_reason,
            "author": comment.author.username,
        }
