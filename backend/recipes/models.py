from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import EmailValidator
from django.db import models

from .validators import validate_username

User = get_user_model()


class CustomUser(AbstractBaseUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            validate_username
        ],
        verbose_name='Логин',
        help_text='Логин'
    )

    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        validators=[
            EmailValidator(
                message="Введите корректный адрес электронной почты."
            )
        ],
        verbose_name='Email',
    )

    def __str__(self):
        return self.username


class MeasurementUnit(models.Model):
    abbreviation = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Сокращение',
    )

    def __str__(self):
        return self.abbreviation

    class Meta:
        verbose_name = "Единица измерения"
        verbose_name_plural = "Единицы измерения"


class Ingredient(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name='Название',
    )

    measurement_unit = models.ForeignKey(
        MeasurementUnit,
        related_name='ingredients',
        on_delete=models.CASCADE,
        verbose_name='Единица измерения',
    )

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]

        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class Tag(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название тега',
    )

    color_code = models.CharField(
        max_length=7,
        unique=True,
        help_text="Например, #49B64E.",
        verbose_name='Цветовой код',
    )

    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг',
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )

    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Заголовок',
    )

    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        blank=True,
        default=None,
        verbose_name='Фотография',
    )

    text = models.TextField(
        verbose_name='Описание',
    )

    cooking_time = models.PositiveIntegerField(
        help_text="Время приготовления в минутах",
        verbose_name='Время приготовления',
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиенты',
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name='Количество',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]

        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"


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

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]

        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"


class ShopList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_shop_recipe'
            )
        ]

        verbose_name = "Рецепт в списке покупок"
        verbose_name_plural = "Рецепты в списке покупок"
