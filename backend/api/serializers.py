from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from customusers.models import Follow
from recipes.models import (
    Tag, Ingredient,
    RecipeIngredient,
    Recipe, FavoriteRecipe,
    ShopList
)
from recipes.validators import validate_color

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


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
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request
                and request.user.is_authenticated
                and request.user.following.filter(author=obj).exists())


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
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    image = serializers.SerializerMethodField()

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

    def get_image(self, obj):
        if obj.image:
            return obj.image.url


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
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise ValidationError("You must provide at least one ingredient.")

        # Проверка наличия хотя бы одного тега
        tags = data.get('tags')
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
        ingredients_to_create = []

        for ingredient in ingredients_data:
            ingredient_obj = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            ingredients_to_create.append(ingredient_obj)

        RecipeIngredient.objects.bulk_create(ingredients_to_create)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            author=request.user,
            **validated_data
        )
        # Добавляем ингредиенты
        self.add_ingredients(ingredients_data, recipe)
        recipe.tags.add(*tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.ingredients.clear()
        instance.tags.clear()
        self.add_ingredients(ingredients_data, instance)
        instance.tags.add(*tags_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        response_serializer = RecipeSerializer(
            instance,
            context=self.context
        )
        return response_serializer.data


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.image:
            return obj.image.url


class FollowUserSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (CustomUserSerializer.Meta.fields
                  + ('recipes', 'recipes_count'))

    def get_recipes(self, obj):
        queryset = obj.recipes.all()
        if recipes_limit := self.context['request'].query_params.get(
                'recipes_limit'
        ):
            queryset = queryset[:int(recipes_limit)]

        # Используем FavoriteRecipeSerializer для сериализации рецептов
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message="Подписка уже существует."
            )
        ]

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user.id == author.id:
            raise serializers.ValidationError(
                "Вы настолько себя любите?"
            )

        return data

    def to_representation(self, instance):
        response_serializer = FollowUserSerializer(
            instance.author,
            context=self.context
        )
        return response_serializer.data


class BaseActionSerializer(serializers.ModelSerializer):

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
        validators = [
            UniqueTogetherValidator(
                queryset=ShopList.objects.all(),
                fields=('user', 'recipe'),
                message="Объект уже существует."
            )
        ]


class FavoriteRecipeSerializer(BaseActionSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=FavoriteRecipe.objects.all(),
                fields=('user', 'recipe'),
                message="Объект уже существует."
            )
        ]
