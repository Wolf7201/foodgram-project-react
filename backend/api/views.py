from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from customusers.models import (
    User,
    Follow,
)
from recipes.models import (
    Tag,
    RecipeIngredient,
    Ingredient,
    Recipe,
    FavoriteRecipe,
    ShopList,
)
from .filters import RecipeFilter, IngredientFilter
from .pagination import CustomPageNumberPagination
from .permissions import AuthorOrReadOnly
from .serializers import (
    TagSerializer, IngredientSerializer,
    RecipeSerializer, RecipeCreateSerializer,
    FollowUserSerializer, ShopListSerializer,
    FavoriteRecipeSerializer, CustomUserSerializer,
    FollowCreateSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    permission_classes = (AuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Recipe.objects.all()
        return Recipe.objects.with_annotations(user)

    @staticmethod
    def get_ingredients_data(user):
        """Получает данные об ингредиентах из базы данных."""
        return RecipeIngredient.objects.filter(
            recipe__shop_list__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

    @staticmethod
    def format_content(ingredients_data):
        """Формирует содержимое файла на основе данных об ингредиентах."""
        return "\n".join(
            f"{idx + 1}. {data['ingredient__name'].capitalize()}, "
            f"{data['total_amount']} {data['ingredient__measurement_unit']}"
            for idx, data in enumerate(ingredients_data)
        )

    @action(detail=False, methods=['GET'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredients_data = self.get_ingredients_data(request.user)
        content = self.format_content(ingredients_data)

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = ('attachment;'
                                           ' filename="shop_list.txt"')
        return response

    def create_relationship(self, recipe_id, serializer_class):
        data = {'user': self.request.user.id, 'recipe': recipe_id}
        serializer = serializer_class(
            data=data,
            context={'request': self.request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_relationship(self, recipe_id, model):
        request = self.request
        recipe = get_object_or_404(Recipe, id=recipe_id)
        count, info = model.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт не найден.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['POST', 'DELETE'], url_path='shopping_cart')
    def shop_list(self, request, pk=None):
        if request.method == 'POST':
            return self.create_relationship(pk, ShopListSerializer)
        return self.delete_relationship(pk, ShopList)

    @action(detail=True, methods=['POST', 'DELETE'], url_path='favorite')
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.create_relationship(pk, FavoriteRecipeSerializer)
        return self.delete_relationship(pk, FavoriteRecipe)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPageNumberPagination
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super(UserViewSet, self).get_permissions()

    @action(detail=False, methods=['GET'], url_path='subscriptions')
    def get_subscriptions(self, request):
        # Получаем всех авторов, на которых подписан текущий пользователь
        users = User.objects.filter(followers__user=request.user)

        # Получаем информацию о каждом авторе с помощью нашего сериализатора
        page = self.paginate_queryset(users)
        serializer = FollowUserSerializer(
            page,
            many=True,
            context={'request': request, 'recipes_limit': 6}
        )
        return self.get_paginated_response(serializer.data)

    def create_relationship(self, user_id, serializer_class):
        author = get_object_or_404(User, id=user_id)
        data = {'user': self.request.user.id, 'author': author.id}
        serializer = serializer_class(
            data=data,
            context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_relationship(self, user_id, model):
        request = self.request
        author = get_object_or_404(User, id=user_id)
        count, info = model.objects.filter(
            user=request.user,
            author=author
        ).delete()
        if count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Подписка не найдена.'},
            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST', 'DELETE'], url_path='subscribe')
    def subscribe(self, request, id):
        if request.method == 'POST':
            return self.create_relationship(id, FollowCreateSerializer)
        return self.delete_relationship(id, Follow)
