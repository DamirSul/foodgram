from rest_framework import serializers, status, validators
from rest_framework.relations import SlugRelatedField
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
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
import base64
from django.core.files.base import ContentFile

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

    # def create(self, validated_data):
    #     user = User(
    #         email=validated_data['email'],
    #         username=validated_data['username']
    #     )
    #     user.set_password(validated_data['password'])
    #     user.save()
    #     return user

    # def validate(self, attrs):
    #     email = attrs.get('email')
    #     password = attrs.get('password')

    #     if email and password:
    #         user = authenticate(request=self.context.get('request'), email=email, password=password)
    #     else:
    #         raise serializers.ValidationError('Must include "email" and "password".')

    #     attrs['user'] = user
    #     return attrs

# class CustomUserCreateSerializer(UserCreateSerializer):
#     username = serializers.CharField(required=True)
#     email = serializers.EmailField(required=True)
#     first_name = serializers.CharField(required=True)
#     last_name = serializers.CharField(required=True)
#     password = serializers.CharField(write_only=True, required=True)
#     class Meta(UserCreateSerializer.Meta):
#         model = User
#         fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password')

#     def create(self, validated_data):
#         password = validated_data.pop('password', None)
#         user = super().create(validated_data)
#         if password:
#             user.set_password(password)
#             user.save()
#         return user

# class UserLoginSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, attrs):
#         email = attrs.get('email')
#         password = attrs.get('password')
#         user = authenticate(email=email, password=password)
#         print(user)
#         if user is None:
#             print('ERRRROOOOOOOOOOOR')
#             raise serializers.ValidationError("Unable to log in with provided credentials.")
#         attrs['user'] = user
#         return attrs

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_subscribed', 'avatar')


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
    ingredient = IngredientSerializer()  # Принимаем название ингредиента, а не ID

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, source='recipeingredient_set')
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'cooking_time', 'image', 'ingredients', 'tags')

# class RecipeIngredientSerializer(serializers.ModelSerializer):
#     ingredient = IngredientSerializer(read_only=True)
#     tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
#     image = Base64ImageField(required=False, allow_null=True)

#     class Meta:
#         model = RecipeIngredient
#         fields = ('ingredient', 'amount')


# class RecipeSerializer(serializers.ModelSerializer):
#     ingredients = RecipeIngredientSerializer(many=True, source='recipeingredient_set', read_only=True)
#     tags = TagSerializer(many=True, read_only=True)
#     image = Base64ImageField(required=False, allow_null=True)

#     class Meta:
#         model = Recipe
#         fields = ('id', 'name', 'text', 'cooking_time', 'image', 'ingredients', 'tags')


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



