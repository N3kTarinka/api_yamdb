from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.fields import CharField, EmailField

from api.validators import username_validator
from reviews.models import Category, Genre, Title, Review, Comment
from users.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        exclude = ('id',)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        exclude = ('id',)


class TitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description',
                  'category', 'genre', 'rating')


class TitleCreateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug', queryset=Genre.objects.all(), many=True
    )

    class Meta:
        model = Title
        fields = ('name', 'year', 'description', 'category', 'genre', 'id')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )


class UserEditSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)


class SignupSerializer(serializers.Serializer):
    username = CharField(
        max_length=settings.USERNAME_LIMIT,
        required=True,
        validators=(username_validator,),
    )
    email = EmailField(
        max_length=settings.EMAIL_LIMIT,
        required=True
    )

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        if User.objects.filter(username=username, email=email).exists():
            return data
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                {'username': 'Имя пользователя уже занято.'})
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {'email': 'Этот адрес электронной почты уже используется.'})
        return data

    def check_user_exists(self, username, email):
        """Проверка существования пользователя."""
        return User.objects.filter(username=username, email=email).exists()


class TokenSerializer(serializers.Serializer):
    username = CharField(
        max_length=settings.USERNAME_LIMIT,
        required=True,
        validators=(username_validator,),
    )
    confirmation_code = CharField(
        max_length=settings.CODE_LIMIT, required=True
    )


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate(self, data):
        if self.context['request'].method == 'POST':
            title_id = self.context['view'].kwargs.get('title_id')
            title = get_object_or_404(Title, id=title_id)
            author = self.context['request'].user

            if Review.objects.filter(title=title, author=author).exists():
                raise serializers.ValidationError(
                    'Вы уже оставили отзыв для этого произведения'
                )
        return data

    def validate_score(self, score):
        if not settings.MIN_SCORE_REVIEW <= score <= settings.MAX_SCORE_REVIEW:
            raise serializers.ValidationError(
                f'Оценка должна быть от {settings.MIN_SCORE_REVIEW} до'
                f' {settings.MAX_SCORE_REVIEW}'
            )
        return score


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username')

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date')
        model = Comment
