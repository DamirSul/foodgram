from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import (
    filters, permissions, status, views, viewsets
)

from food.models import (
    User,
    Tag,
    Recipe,
    Purchase,
    Favorite,
    Subscription,
    Ingredient,
    RecipeIngredient
)
from .serializers import (
    UserSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeIngredientSerializer,
    TagSerializer,
    PurchaseSerializer,
    SubscriptionSerializer,
    RecipeSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Favorite ViewSet
class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

# Tag ViewSet
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

# Recipe ViewSet
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

# Purchase ViewSet
class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer

# Subscription ViewSet
class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

# Ingredient ViewSet
class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

# RecipeIngredient ViewSet
class RecipeIngredientViewSet(viewsets.ModelViewSet):
    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer

