from rest_framework import serializers, status, validators
from rest_framework.relations import SlugRelatedField
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from food.models import (
    User,
    Tag,
    Recipe,
    Purchases,
    Favorites,
    Subscriptions,
    Ingredient,
    RecipeIngredient
)


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_subscribed', 'avatar')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, source='recipeingredient_set', read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'cooking_time', 'image', 'ingredients', 'tags')


class PurchasesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Purchases
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoritesSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = Favorites
        fields = ('id', 'user', 'recipe')


class SubscriptionsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    subscribed_to = UserSerializer(read_only=True)

    class Meta:
        model = Subscriptions
        fields = ('id', 'user', 'subscribed_to')