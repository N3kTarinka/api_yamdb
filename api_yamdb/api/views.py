import uuid
from django.db.models import Avg
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError
from rest_framework.decorators import action, api_view
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Title, Review
from users.models import User
from rest_framework import filters, status, viewsets
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import (DjangoFilterBackend,
                                           CharFilter, FilterSet)

from .serializers import (CategorySerializer, TokenSerializer,
                          SignupSerializer, UserEditSerializer,
                          UserSerializer, GenreSerializer,
                          TitleSerializer, TitleCreateSerializer,
                          ReviewSerializer, CommentSerializer)
from .permissions import (IsAdmin, IsAdminOrReadOnly,
                          IsUserAdminModeratorOrReadOnly)


class BanPutHeadOptionsMethodsMixinViewSet(viewsets.ModelViewSet):
    http_method_names = ('get', 'patch', 'post', 'delete')

class BaseReviewViewSet(BanPutHeadOptionsMethodsMixinViewSet):
    permission_classes = (IsUserAdminModeratorOrReadOnly,)

    def get_instance(self, model, pk):
        return get_object_or_404(model, pk=pk)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

    def retrieve(self, request, *args, **kwargs):
        # Отключаем доступ к retrieve и возвращаем 405
        return Response(
            {'detail': 'Method Not Allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        # Отключаем PATCH запросы и возвращаем 405
        return Response(
            {'detail': 'Method Not Allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all().order_by('id')
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = PageNumberPagination
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']  # Настройка поиска по полю name

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

    def partial_update(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        if not Genre.objects.filter(slug=slug).exists():
            return Response(
                {'detail': 'Method Not Allowed'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().partial_update(request, *args, **kwargs)


class TitleFilter(FilterSet):
    genre = CharFilter(field_name='genre__slug')
    category = CharFilter(field_name='category__slug')

    class Meta:
        model = Title
        fields = ['category', 'genre', 'name', 'year']


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return TitleCreateSerializer
        return TitleSerializer

    def update(self, request, *args, **kwargs):
        # Block PUT requests by returning a 405 status
        if request.method == 'PUT':
            return Response(
                {'detail': 'Method Not Allowed'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_admin:
            return super().partial_update(request, *args, **kwargs)
        return Response(
            {'detail': 'Method Not Allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def get_queryset(self):
        queryset = (
            Title.objects.all().annotate(rating=Avg('reviews__score'))
            .order_by('rating')
        )
        return queryset


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
        username = serializer.validated_data.get('username')
        email = serializer.validated_data.get('email')
        user, _ = User.objects.get_or_create(username=username, email=email)
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
