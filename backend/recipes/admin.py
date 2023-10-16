from django.contrib import admin

from .models import (
    MeasurementUnit,
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    Follow,
    FavoriteRecipe,
    ShopList,
)


class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ('pk', 'abbreviation',)
    search_fields = ('abbreviation',)
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color_code', 'slug',)
    search_fields = ('name', 'slug',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author', 'cooking_time',)
    search_fields = ('name', 'author__username',)
    list_filter = ('tags', 'author',)
    empty_value_display = '-пусто-'


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount',)
    search_fields = ('recipe__name', 'ingredient__name',)
    list_filter = ('recipe', 'ingredient',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author',)
    search_fields = ('user__username', 'author__username',)
    empty_value_display = '-пусто-'


class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)
    empty_value_display = '-пусто-'


class ShopListAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)
    empty_value_display = '-пусто-'


admin.site.register(MeasurementUnit, MeasurementUnitAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(FavoriteRecipe, FavoriteRecipeAdmin)
admin.site.register(ShopList, ShopListAdmin)
