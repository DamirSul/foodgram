from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import redirect_to_recipe
from .views import UserViewSet, RecipeViewSet, IngredientViewSet, TagViewSet, ShoppingCartViewSet
from django.views.generic import TemplateView


api_v1 = DefaultRouter()
api_v1.register(r'users', UserViewSet, basename='users')
api_v1.register(r'recipes', RecipeViewSet, basename='recipes')
api_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')
api_v1.register(r'tags', TagViewSet, basename='tags')
api_v1.register(r'shopping_cart', ShoppingCartViewSet, basename='shopping_cart')


urlpatterns = [
    path('', include(api_v1.urls)),
    path('s/<str:short_code>/', redirect_to_recipe, name='short-link'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('docs/', TemplateView.as_view(template_name=r'redoc.html'), name='redoc')

]
