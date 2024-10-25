from django.urls import path
from django.contrib import admin
from ninja import NinjaAPI
from users.views import router as users_router
from posts.views.views_posts import router as posts_router
from posts.views.views_comments import router as comments_router
from posts.views.views_analytics import router as analytics_router

api = NinjaAPI()

api.add_router("/users/", users_router)
api.add_router("/posts/", posts_router)
api.add_router("/posts/comments/", comments_router)
api.add_router("/posts/analytics/", analytics_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
