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




# class RecipeIngredientSerializer(serializers.ModelSerializer):
#     id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

#     class Meta:
#         model = RecipeIngredient
#         fields = ['id', 'amount']



# class RecipeSerializer(serializers.ModelSerializer):
#     #ingredients = RecipeIngredientSerializer(many=True)
#     tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
#     image = Base64ImageField(required=False, allow_null=True)
#     author = serializers.ReadOnlyField(source='author.username')

#     class Meta:
#         model = Recipe
#         fields = ['id', 'name', 'text', 'cooking_time', 'image', 'ingredients', 'tags', 'author']



class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), source='ingredient.id')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']

    def to_representation(self, instance):
        """Переопределяем вывод данных."""
        representation = super().to_representation(instance)
        representation['id'] = instance.ingredient.id  # Явно указываем ID ингредиента
        representation['name'] = instance.ingredient.name  # Добавляем название ингредиента для удобства
        return representation



class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=False, allow_null=True)
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'text', 'cooking_time', 'image', 'ingredients', 'tags', 'author']

    def create(self, validated_data):
        # Убираем ингредиенты и теги из validated_data
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        user = self.context['request'].user
        
        # Создаем рецепт
        recipe = Recipe.objects.create( **validated_data)

        print(f"Recipe created: {recipe}")
        print(f"Received ingredients data: {ingredients_data}")

        # Добавляем теги к рецепту
        recipe.tags.set(tags_data)
        
        # Добавляем ингредиенты к рецепту
        for ingredient_data in ingredients_data:
            print(f"Current ingredient data: {ingredient_data}")  # Отладочный вывод
            if 'id' not in ingredient_data:
                print(f"Error: 'id' key not found in ingredient_data: {ingredient_data}")  # Сообщение об ошибке
                continue  # Пропускаем текущий ингредиент, если нет 'id'

            # Пытаемся получить ингредиент по ID
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            print(f"Found ingredient: {ingredient}")
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )
            print(f"RecipeIngredient created: {ingredient} with amount {ingredient_data['amount']}")
        
        return recipe






























           
            # for ingredient_data in ingredients_data:
            #     print("Current ingredient data:", ingredient_data)  # Отладочный вывод для каждого ингредиента

            #     # Попробуем отладить получение id ингредиента
            #     ingredient = ingredient_data['ingredient']
            #     print("Ingredient ID:", ingredient.id)  # Отладочный вывод ID ингредиента
            #     print("Ingredient amount:", ingredient_data['amount'])  # Отладочный вывод количества

            #     # Создание записи для ингредиента рецепта
            #     RecipeIngredient.objects.create(
            #         recipe=recipe,
            #         ingredient=ingredient,
            #         amount=ingredient_data['amount']
            #     )

            # print("Recipe created successfully:", recipe.id)  # Отладочный вывод ID рецепта

            # return recipe



















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



