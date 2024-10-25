from celery import shared_task
from django.http import JsonResponse

from posts.ai_tools import generate_relevant_reply
from posts.models import Comment, Post


@shared_task
def send_auto_reply(post_id, comment_id):
    try:
        post = Post.objects.get(id=post_id)
        comment = Comment.objects.get(id=comment_id)

        # Relevant answer generate
        reply_content = generate_relevant_reply(post, comment)

        # Comment create
        comment = Comment.objects.create(
            author=post.author,
            post=post,
            content=reply_content,
            parent=comment,
        )
        print(f"Auto reply has been created: {comment.content}")
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)

    except Comment.DoesNotExist:
        return JsonResponse({"error": "Comment not found"}, status=404)
