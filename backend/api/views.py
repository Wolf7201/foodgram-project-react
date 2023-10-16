from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .permissions import AdminOrReadOnly, AuthorOrAdminOrReadOnly
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeCreateSerializer,
    FavoriteRecipeSerializer,
    FollowUserSerializer
)
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    FavoriteRecipe,
    User,
    Follow,
    ShopList,
    RecipeIngredient,
)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('id')

    serializer_class = RecipeSerializer
    filterset_fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')
    permission_classes = (AuthorOrAdminOrReadOnly,)

    def create(self, request, *args, **kwargs):
        # Используем сериализатор для создания рецепта для проверки и сохранения данных
        create_serializer = RecipeCreateSerializer(data=request.data)
        if create_serializer.is_valid():
            # Мы добавляем автора из запроса
            recipe = create_serializer.save(author=self.request.user)
            # Теперь используем основной сериализатор для формирования ответа
            response_serializer = RecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            create_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def partial_update(self, request, *args, **kwargs):
        recipe = self.get_object()
        update_serializer = RecipeCreateSerializer(
            recipe,
            data=request.data,
            partial=True
        )  # учитываем, что это частичное обновление
        if update_serializer.is_valid():
            updated_recipe = update_serializer.save()
            response_serializer = RecipeSerializer(
                updated_recipe,
                context={'request': request}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(
            update_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['GET'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user_recipes = ShopList.objects.filter(
            user_id=request.user.id
        ).values_list(
            'recipe_id',
            flat=True
        )

        # Производим запрос к базе данных для получения
        # всех ингредиентов для данных рецептов
        ingredients_info = RecipeIngredient.objects.filter(
            recipe_id__in=user_recipes
        ).select_related(
            'ingredient',
            'ingredient__measurement_unit'
        )

        shop_list = {}

        for ri in ingredients_info:
            ingredient = ri.ingredient.name
            amount = int(ri.amount)
            unit = ri.ingredient.measurement_unit.abbreviation

            if ingredient in shop_list:
                shop_list[ingredient]['amount'] += amount
            else:
                shop_list[ingredient] = {
                    'amount': amount,
                    'unit': unit
                }

        content = "\n".join(
            f"{i}. {key.capitalize()}, {value['amount']} {value['unit']}"
            for i, (key, value) in enumerate(shop_list.items(), start=1)
        )

        # Создаем HttpResponse
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shop_list.txt"'

        return response

    @action(detail=True, methods=['POST', 'DELETE'], url_path='shopping_cart')
    def shop_list(self, request, pk=None):
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=pk)

            # Проверка на наличие рецепта в избранном
            if ShopList.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ShopList.objects.create(user=request.user, recipe=recipe)

            serializer = FavoriteRecipeSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            # Попытаемся найти рецепт в избранном и удалить его
            try:
                shop_list = ShopList.objects.get(user=request.user, recipe_id=pk)
                shop_list.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ShopList.DoesNotExist:
                return Response(
                    {'detail': 'Рецепт не найден в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=True, methods=['POST', 'DELETE'], url_path='favorite')
    def favorite(self, request, pk=None):

        if request.method == 'POST':
            # Проверка существования рецепта
            recipe = get_object_or_404(Recipe, id=pk)
            # Проверка на наличие рецепта в избранном
            if FavoriteRecipe.objects.filter(
                    user=request.user,
                    recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            FavoriteRecipe.objects.create(
                user=request.user,
                recipe=recipe
            )

            serializer = FavoriteRecipeSerializer(
                recipe,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            try:
                favorite_recipe = FavoriteRecipe.objects.get(
                    user=request.user,
                    recipe_id=pk
                )
                favorite_recipe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except FavoriteRecipe.DoesNotExist:
                return Response(
                    {'detail': 'Рецепт не найден в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )


class FollowUserViewSet(viewsets.ViewSet):
    queryset = User.objects.all()

    @action(detail=False, methods=['GET'], url_path='subscriptions')
    def get_subscriptions(self, request):
        # Получаем всех авторов, на которых подписан текущий пользователь
        followed_users = (request.user.following.all()
                          .values_list('author', flat=True))
        users = User.objects.filter(id__in=followed_users)

        # Получаем информацию о каждом авторе с помощью нашего сериализатора
        serializer = FollowUserSerializer(
            users,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST', 'DELETE'], url_path='subscribe')
    def subscribe(self, request, pk):

        if request.method == 'POST':
            # Проверка существования пользователя
            author = get_object_or_404(User, id=pk)

            # Проверка на наличие пользователя в подписках
            if Follow.objects.filter(user=request.user, author=author).exists():
                return Response(
                    {'errors': 'Автор уже в подписках.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Follow.objects.create(user=request.user, author=author)

            serializer = FollowUserSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            # Попытаемся найти подписку на автора и удалить его
            try:
                follow = Follow.objects.get(user=request.user, author=pk)
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Follow.DoesNotExist:
                return Response(
                    {'detail': 'Не найдена подписка на автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
