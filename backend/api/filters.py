from django_filters.rest_framework import (
    FilterSet,
    AllValuesMultipleFilter,
    BooleanFilter, CharFilter,
)

from recipes.models import Recipe, Ingredient


class RecipeFilter(FilterSet):
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_in_shopping_cart = BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    is_favorited = BooleanFilter(
        method='filter_is_favorited'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags',
                  'is_in_shopping_cart',
                  'is_favorited')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shop_list__user=user)
        return queryset


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
