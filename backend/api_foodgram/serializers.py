import base64

from rest_framework import serializers, status, validators
from rest_framework.relations import SlugRelatedField
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, TokenCreateSerializer
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



User = get_user_model()

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Если данные пустые, возвращаем пустое значение
        if not data:
            return super().to_internal_value(data)

        # Если данные в формате Base64, декодируем их
        if isinstance(data, str):
            # Проверяем, содержит ли строка метаданные
            if data.startswith('data:image'):
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                # Создаем временный файл
                data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        
        return super().to_internal_value(data)


class CustomTokenCreateSerializer(TokenCreateSerializer):
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['email', 'password']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user



class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='ingredient', queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')  # id ссылается на Ingredient, а amount на RecipeIngredient




class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'cooking_time', 'image', 'ingredients', 'tags')

    def validate(self, data):
        print("Validation step:", data)
        return data
    
    def create(self, validated_data):
        # Убираем ингредиенты и теги из валидированных данных
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        # Извлекаем текущего пользователя (автора рецепта) из контекста запроса
        user = self.context['request'].user

        # Создаем рецепт с автором
        recipe = Recipe.objects.create(author=user, **validated_data)

        # Устанавливаем теги
        recipe.tags.set(tags_data)

        # Обрабатываем ингредиенты
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],  # Используйте 'ingredient', так как у нас 'source'
                amount=ingredient_data['amount']           # Количество ингредиента
            )

        return recipe









# class RecipeIngredientSerializer(serializers.ModelSerializer):
#     ingredient = IngredientSerializer() PK

#     class Meta:
#         model = RecipeIngredient
#         fields = ('ingredient', 'amount')




class PurchaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Purchase
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')


class SubscriptionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    subscribed_to = UserSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ('id', 'user', 'subscribed_to')



