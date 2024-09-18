from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet,
    FavoriteViewSet,
    TagViewSet,
    RecipeViewSet,
    PurchaseViewSet,
    SubscriptionViewSet,
    IngredientViewSet,
    
)
from .views import UserTokenObtainView
app_name = 'api_v1'

router_v1 = routers.DefaultRouter()
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')


api_v1 = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls')),  # Для регистрации и работы с пользователями
    path('auth/', include('djoser.urls.authtoken')),  # Для получения токенов
    # path('auth/token/login/', LoginView, name='token_obtain'),
]

urlpatterns = [
    path('v1/', include(api_v1)),
]