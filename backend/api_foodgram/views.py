from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import (
    filters, permissions, status, views, viewsets
)
from django.shortcuts import get_object_or_404
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
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token

from rest_framework import views, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from api_foodgram.serializers import CustomTokenCreateSerializer

class UserTokenObtainView(views.APIView):
    permission_classes = (AllowAny,)  # Доступен всем пользователям

    def post(self, request):
        serializer = CustomTokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']  # Получаем пользователя после валидации

        # Генерация или получение существующего токена
        token, created = Token.objects.get_or_create(user=user)

        return Response({'token': token.key}, status=status.HTTP_200_OK)

    

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api_foodgram.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'PATCH':  # Исправлено с 'PUT' на 'PATCH'
            serializer = self.get_serializer(
                request.user,
                data=request.data,
                partial=True  # Частичное обновление
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)



# Favorite ViewSet
class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

# Tag ViewSet
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

# # Recipe ViewSet
# class RecipeViewSet(viewsets.ModelViewSet):
#     queryset = Recipe.objects.all()
#     serializer_class = RecipeSerializer
from rest_framework.permissions import IsAuthenticated

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]  # Только аутентифицированные пользователи

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# Ingredient ViewSet
class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

# RecipeIngredient ViewSet
class RecipeIngredientViewSet(viewsets.ModelViewSet):
    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer
    


# Purchase ViewSet
class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer

# Subscription ViewSet
class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer



