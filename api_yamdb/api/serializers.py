from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import CharField, EmailField
from reviews.models import Category, Genre, Title
from users.models import User
from users.validators import username_validator


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['name', 'slug']  # Поля, необходимые по документации



class TitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'category', 'genre')


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

    def validate_username(self, value):
        return username_validator(value)


class TokenSerializer(serializers.Serializer):
    username = CharField(
        max_length=settings.USERNAME_LIMIT,
        required=True,
        validators=(username_validator,),
    )
    confirmation_code = CharField(
        max_length=settings.CODE_LIMIT, required=True
    )

    def validate_username(self, value):
        return username_validator(value)
