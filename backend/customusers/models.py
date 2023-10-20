from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models

MAX_LENGTH_TEXT_FIELD = 150
MAX_LENGTH_EMAIL = 254


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Email field is required.")
        user = self.model(
            email=self.normalize_email(email),
            **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)

        return self.create_user(**kwargs)


# Custom User Model.
class CustomUser(AbstractUser):
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        verbose_name='Email',
    )
    username = models.CharField(
        max_length=MAX_LENGTH_TEXT_FIELD,
        unique=True,
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

    objects = UserManager()

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = [
        'first_name',
        'last_name',
        'username',
    ]

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['id']
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Follow(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Пользователь',
    )

    author = models.ForeignKey(
        CustomUser,
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
        ordering = ['id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
