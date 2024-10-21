from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (CategoryViewSet, GenreViewSet, TitleViewSet,
                       UserViewSet, CommentViewSet, ReviewViewSet)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'titles', TitleViewSet)
router.register(r'users', UserViewSet)
router.register(
    r'titles/(?P<title_id>[\d]+)/reviews',
    ReviewViewSet,
    basename='reviews'
)
router.register(
    r'titles/(?P<title_id>[\d]+)/reviews/(?P<review_id>[\d]+)/comments',
    CommentViewSet,
    basename='comments',
)

urlpatterns = [
    path('v1/auth/', include('users.urls')),
    path('v1/', include(router.urls)),
]
