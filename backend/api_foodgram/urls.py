from django.urls import include, path
from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet,
    FavoriteViewSet,
    TagViewSet,
    RecipeViewSet,
    PurchaseViewSet,
    SubscriptionViewSet,
    IngredientViewSet
)

app_name = 'api_v1'

router_v1 = routers.DefaultRouter()
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')


api_v1 = [
    path('', include(router_v1.urls))
]

urlpatterns = [
    path('v1/', include(api_v1)),
]
