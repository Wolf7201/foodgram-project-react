from django.contrib import admin

from .models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    FavoriteRecipe,
    ShopList,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color_code', 'slug',)
    search_fields = ('name', 'slug',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author', 'cooking_time',)
    search_fields = ('name', 'author__username',)
    list_filter = ('tags', 'author',)
    inlines = [RecipeIngredientInline]
    empty_value_display = '-пусто-'


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount',)
    search_fields = ('recipe__name', 'ingredient__name',)
    list_filter = ('recipe', 'ingredient',)
    empty_value_display = '-пусто-'

    @admin.display(description='Количество добавлений в избранное')
    def number_of_favorites(self, obj):
        return FavoriteRecipe.objects.filter(recipe=obj).count()


class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)
    empty_value_display = '-пусто-'


class ShopListAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)
    empty_value_display = '-пусто-'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(FavoriteRecipe, FavoriteRecipeAdmin)
admin.site.register(ShopList, ShopListAdmin)
