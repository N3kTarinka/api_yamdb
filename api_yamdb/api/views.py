import uuid

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from api.filter import TitleFilter
from api.permissions import (IsAdmin, IsAdminOrReadOnly,
                             IsUserAdminModeratorOrReadOnly)
from api.serializers import (CategorySerializer, TokenSerializer,
                             UserEditSerializer, UserSerializer,
                             GenreSerializer, TitleSerializer,
                             TitleCreateSerializer, SignupSerializer,
                             ReviewSerializer, CommentSerializer)
from reviews.models import Category, Genre, Title, Review
from users.models import User




class BanPutHeadOptionsMethodsMixinViewSet(viewsets.ModelViewSet):
    http_method_names = ('get', 'patch', 'post', 'delete')


class BaseReviewViewSet(BanPutHeadOptionsMethodsMixinViewSet):
    permission_classes = (IsUserAdminModeratorOrReadOnly,)

    def get_instance(self, model, pk):
        return get_object_or_404(model, pk=pk)

class CategoryGenreMixinViewSet(viewsets.ModelViewSet):
    http_method_names = ('get', 'post', 'delete')
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = PageNumberPagination
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

class CategoryViewSet(CategoryGenreMixinViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer

    def retrieve(self, request, *args, **kwargs):
        # Отключаем доступ к retrieve и возвращаем 405
        return Response(
            {'detail': 'Method Not Allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class GenreViewSet(CategoryGenreMixinViewSet):
    queryset = Genre.objects.all().order_by('id')
    serializer_class = GenreSerializer

    def retrieve(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        if not Genre.objects.filter(slug=slug).exists():
            return Response(
                {'detail': 'Method Not Allowed'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TitleViewSet(BanPutHeadOptionsMethodsMixinViewSet):
    queryset = Title.objects.all().annotate(
        rating=Avg('reviews__score')).order_by('rating')
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return TitleCreateSerializer
        return TitleSerializer


class UserViewSet(BanPutHeadOptionsMethodsMixinViewSet):
    lookup_field = 'username'
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAdmin,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated,),
        serializer_class=UserEditSerializer,
    )
    def users_own_profile(self, request):
        user = request.user
        if request.method == 'PATCH':
            serializer = self.get_serializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewViewSet(BaseReviewViewSet):
    serializer_class = ReviewSerializer

    def fetch_title(self):
        return self.get_instance(Title, self.kwargs['title_id'])

    def perform_create(self, serializer):
        title = self.fetch_title()
        serializer.save(author=self.request.user, title=title)

    def get_queryset(self):
        return self.fetch_title().reviews.all()


class CommentViewSet(BaseReviewViewSet):
    serializer_class = CommentSerializer

    def fetch_review(self):
        return self.get_instance(Review, self.kwargs['review_id'])

    def perform_create(self, serializer):
        review = self.fetch_review()
        serializer.save(author=self.request.user, review=review)

    def get_queryset(self):
        return self.fetch_review().comments.all()


@api_view(['POST'])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user, _ = User.objects.get_or_create(**serializer.validated_data)
    except IntegrityError:
        return Response(
            settings.LOGIN_OR_EMAIL_ERROR, status.HTTP_400_BAD_REQUEST
        )
    confirmation_code = str(uuid.uuid4())
    send_mail(
        subject='Регистрация в проекте YaMDb',
        message=f'Ваш проверочный код: {confirmation_code}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User, username=serializer.validated_data.get('username')
    )
    if default_token_generator.check_token(
        user, serializer.validated_data.get('confirmation_code')
    ):
        token = AccessToken.for_user(user)
        return Response({'token': str(token)}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
