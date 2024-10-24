from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from api.validators import username_validator


class User(AbstractUser):
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    USER = 'user'
    ROLE_CHOICES = (
        (USER, 'Пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Администратор'),
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=settings.USERNAME_LIMIT,
        unique=True,
        validators=(username_validator,),
        error_messages={
            'unique': 'Пользователь с таким именем уже существует!',
        },
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=settings.EMAIL_LIMIT,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким email уже существует!',
        },
    )
    first_name = models.CharField(
        'Имя',
        max_length=settings.FIRSTNAME_LIMIT,
        blank=True
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=settings.LASTNAME_LIMIT,
        blank=True
    )
    bio = models.TextField(
        'Биография',
        blank=True
    )
    role = models.CharField(
        'Роль',
        default=USER,
        max_length=max(len(role) for role, _ in ROLE_CHOICES),
        choices=ROLE_CHOICES,
    )

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser or self.is_staff

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        constraints = [
            models.CheckConstraint(
                check=~models.Q(username='me'), name='name_not_me'
            )
        ]

    def __str__(self):
        return self.username[: settings.OUTPUT_LENGTH]
