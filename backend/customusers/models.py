from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models

username_validator = ASCIIUsernameValidator()
MAX_LENGTH_TEXT_FIELD = 150
MAX_LENGTH_EMAIL = 254


class User(AbstractUser):
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        verbose_name='Email',
    )
    username = models.CharField(
        max_length=MAX_LENGTH_TEXT_FIELD,
        unique=True,
        validators=[username_validator],
        verbose_name='Логин',
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_TEXT_FIELD,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_TEXT_FIELD,
        verbose_name='Фамилия',
    )

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = [
        'first_name',
        'last_name',
        'username',
    ]

    def __str__(self):
        return self.email

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Пользователь',
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Автор',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author',
            )
        ]
        ordering = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
