from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import CharField, EmailField
from api.validators import username_validator
from reviews.models import Category, Genre, Title
from users.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')



class TitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'category', 'genre')

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
    email = EmailField(max_length=settings.EMAIL_LIMIT, required=True)


class TokenSerializer(serializers.Serializer):
    username = CharField(
        max_length=settings.USERNAME_LIMIT,
        required=True,
        validators=(username_validator,),
    )
    confirmation_code = CharField(
        max_length=settings.CODE_LIMIT, required=True
    )
