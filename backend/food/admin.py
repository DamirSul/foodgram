from django.contrib import admin
from django.db.models import Count

from users.models import User
from food.models import (
    ShoppingCart,
    Favorite,
    Subscription,
    RecipeIngredient,
    Recipe,
    Ingredient,
    Tag,
)

admin.site.register(
    (ShoppingCart, Favorite, Subscription, RecipeIngredient),
    admin.ModelAdmin,
)


class UserAdmin(admin.ModelAdmin):
    search_fields = ["email", "username"]


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "favorite_count")
    search_fields = ["name", "author__username"]
    list_filter = ("tags",)
    inlines = [RecipeIngredientInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(favorite_count=Count("favorited_recipes"))
        return qs

    def favorite_count(self, obj):
        return obj.favorite_count

    favorite_count.short_description = "Количество в избранном"


class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ["name"]


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ["name"]


admin.site.register(User, UserAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
