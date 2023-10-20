from django.db import models
from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from customusers.models import CustomUser
from django.db.models import OuterRef, Exists

MAX_LENGTH_TEXT_FIELD = 200


class RecipeManager(models.Manager):
    def with_annotations(self, user):
        favorites_subquery = FavoriteRecipe.objects.filter(
            user=user,
            recipe=OuterRef('pk')
        )

        shoplist_subquery = ShopList.objects.filter(
            user=user,
            recipe=OuterRef('pk')
        )

        return self.annotate(
            is_favorited=Exists(favorites_subquery),
            is_in_shopping_cart=Exists(shoplist_subquery)
        )


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_TEXT_FIELD,
        verbose_name='Название',
    )

    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_TEXT_FIELD,
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
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_TEXT_FIELD,
        unique=True,
        verbose_name='Название тега',
    )

    color_code = ColorField(
        unique=True,
        help_text="Например, #49B64E.",
        verbose_name='Цветовой код'
    )

    slug = models.SlugField(
        max_length=MAX_LENGTH_TEXT_FIELD,
        unique=True,
        verbose_name='Слаг',
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Recipe(models.Model):
    objects = RecipeManager()

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )

    name = models.CharField(
        max_length=MAX_LENGTH_TEXT_FIELD,
        verbose_name='Заголовок',
    )

    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Фотография',
    )

    text = models.TextField(
        verbose_name='Описание',
    )

    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Время приготовления в минутах',
        verbose_name='Время приготовления',
    )

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['created']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'


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

    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]
        ordering = ['recipe']
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        default_related_name = 'recipe_ingredients'


class BaseRecipeRelation(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        ordering = ['id']


class FavoriteRecipe(BaseRecipeRelation):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorite_recipes'


class ShopList(BaseRecipeRelation):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_shop_recipe'
            )
        ]
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        default_related_name = 'shop_list'
