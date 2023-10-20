from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction

from customusers.models import (
    CustomUser,
    Follow,
)
from recipes.models import (
    Tag, Ingredient,
    RecipeIngredient,
    Recipe, FavoriteRecipe,
    ShopList
)
from .validators import validate_color


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class TagSerializer(serializers.ModelSerializer):
    color = serializers.CharField(
        source='color_code',
        validators=[validate_color]
    )

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = (self.context.get('request').user
                if self.context.get('request') else None)

        if user and user.is_authenticated:
            return user.following.filter(author=obj).exists()

        return False


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True
    )
    is_favorited = serializers.SerializerMethodField(default='False')
    is_in_shopping_cart = serializers.SerializerMethodField(default='False')
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if hasattr(obj, 'is_favorited'):
            return (request
                    and request.user.is_authenticated
                    and obj.is_favorited)
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if hasattr(obj, 'is_in_shopping_cart'):
            return (request
                    and request.user.is_authenticated
                    and obj.is_in_shopping_cart)
        return False


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        # Проверка наличия хотя бы одного ингредиента
        ingredients = self.initial_data.get('ingredients', [])
        if not ingredients:
            raise ValidationError("You must provide at least one ingredient.")

        # Проверка наличия хотя бы одного тега
        tags = data.get('tags', [])
        if not tags:
            raise ValidationError("You must provide at least one tag.")

        if len(ingredients) != len(
                {ingredient['id'] for ingredient in ingredients}
        ):
            raise serializers.ValidationError("Ingredients must be unique.")

        # Проверка уникальности тегов
        if len(tags) != len(set(tags)):
            raise ValidationError("Tags must be unique.")
        return data

    def validate_image(self, value):
        if not value:
            raise ValidationError("Image is required.")
        return value

    @staticmethod
    def add_ingredients(ingredients_data, recipe):
        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        # Создаем рецепт
        recipe = Recipe.objects.create(
            author=request.user,
            **validated_data
        )
        # Добавляем ингредиенты
        self.add_ingredients(ingredients_data, recipe)

        recipe.tags.add(*tags_data)

        return recipe

    def update(self, instance, validated_data):
        """
        Вопросик, у нас есть валидация, она не пропускает
        данные, если у нас нет полей с тегами и ингредиентами,
        но тут то у нас метод patch, который подразумевает
        возможность частичного изменения данных. Как так?

        """

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        instance.ingredients.clear()
        instance.tags.clear()

        self.add_ingredients(ingredients_data, instance)
        instance.tags.add(*tags_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        response_serializer = RecipeSerializer(instance, context=self.context)
        return response_serializer.data


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowUserSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (CustomUserSerializer.Meta.fields
                  + ('recipes', 'recipes_count'))

    def get_recipes(self, obj):
        if recipes_limit := self.context['request'].query_params.get(
                'recipes_limit'
        ):
            queryset = obj.recipes.all()[:int(recipes_limit)]
        else:
            queryset = obj.recipes.all()

        # Используем FavoriteRecipeSerializer для сериализации рецептов
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        print(user, author)
        if user.id == author:
            raise serializers.ValidationError(
                "Вы настолько себя любите?"
            )

        if self.Meta.model.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                "Подписка уже существует."
            )
        return data

    def to_representation(self, instance):
        response_serializer = FollowUserSerializer(
            instance.author,
            context=self.context
        )
        return response_serializer.data


class BaseActionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Объект уже существует."
            )
        return data

    def to_representation(self, instance):
        response_serializer = ShortRecipeSerializer(
            instance.recipe,
            context=self.context
        )
        return response_serializer.data


class ShopListSerializer(BaseActionSerializer):
    class Meta:
        model = ShopList
        fields = ('user', 'recipe')


class FavoriteRecipeSerializer(BaseActionSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')
