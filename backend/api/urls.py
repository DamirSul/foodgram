from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    RecipeViewSet,
    IngredientViewSet,
    TagViewSet,
    ShoppingCartViewSet,
)

api_v1 = DefaultRouter()
api_v1.register("users", UserViewSet, basename="users")
api_v1.register("recipes", RecipeViewSet, basename="recipes")
api_v1.register(
    "ingredients", IngredientViewSet, basename="ingredients"
)
api_v1.register("tags", TagViewSet, basename="tags")
api_v1.register(
    "shopping_cart", ShoppingCartViewSet, basename="shopping_cart"
)


urlpatterns = [
    path("", include(api_v1.urls)),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path(
        "docs/openapi-schema.yml",
        TemplateView.as_view(template_name=r"redoc.html"),
        name="redoc",
    ),
]
