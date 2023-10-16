import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .validators import validate_color, validate_email_format
from recipes.models import (User, Tag, Ingredient,
                            MeasurementUnit, RecipeIngredient,
                            Recipe, FavoriteRecipe, ShopList)


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.CharField(
        source='measurement_unit.abbreviation'
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

    def create(self, validated_data):
        unit, created_unit = MeasurementUnit.objects.get_or_create(
            abbreviation=validated_data['measurement_unit']['abbreviation']
        )
        ingredient, created_ingredient = Ingredient.objects.get_or_create(
            name=validated_data['name'],
            measurement_unit=unit
        )

        if created_ingredient:
            return ingredient

        raise serializers.ValidationError('Такой ингредиент уже существует!')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit.abbreviation'
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
    # Добавляем поле is_subscribed, которое будет указывать на подписку
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
        # Получаем текущего пользователя, если есть
        user = self.context.get('request').user \
            if self.context.get('request') else None

        # Проверяем, подписан ли текущий пользователь на объект пользователя (obj)
        if user and user.is_authenticated:
            return user.following.filter(author=obj).exists()

        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            validate_email_format
        ]
    )

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password')


class Base64ImageField(serializers.ImageField):
    def to_representation(self, value):
        print(value)
        return value

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_img, imgstr = data.split(';base64,')
            ext = format_img.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')

        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
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
        user = self.context.get('request').user
        return FavoriteRecipe.objects.filter(
            user=user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return ShopList.objects.filter(user=user, recipe=obj).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField(required=False, allow_null=True)

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

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        # Создаем рецепт
        recipe = Recipe.objects.create(**validated_data)

        # Добавляем ингредиенты и теги
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )

        for tag_data in tags_data:
            recipe.tags.add(tag_data)

        return recipe

    def update(self, instance, validated_data):
        if ingredients_data := validated_data.pop('ingredients', None):
            # Удаление всех существующих ингредиентов рецепта
            RecipeIngredient.objects.filter(recipe=instance).delete()
            # Добавление новых ингредиентов
            for ingredient_data in ingredients_data:
                ingredient = Ingredient.objects.get(id=ingredient_data['id'])
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ingredient_data['amount'],
                )

            if tags_data := validated_data.pop('tags', None):
                instance.tags.set(tags_data)

            # Обновление основных полей рецепта
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()

            return instance


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowUserSerializer(CustomUserSerializer):
    recipes = FavoriteRecipeSerializer(read_only=True, many=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (CustomUserSerializer.Meta.fields
                  + ('recipes', 'recipes_count'))

    def get_recipes_count(self, obj):
        return obj.recipes.count()
