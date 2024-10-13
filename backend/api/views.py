import random
import string
import base64

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.core.files.base import ContentFile
from django.db.models import Exists, OuterRef, Value
from django.db import models
from django.http import HttpResponse
from django.conf import settings

from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from rest_framework import status, viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action

from food.models import (
    Ingredient,
    Tag,
    Recipe,
    Subscription,
    Favorite,
    ShoppingCart,
    ShortLink,
)
from users.models import User
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeSerializer,
    FavoriteSerializer,
    UserSerializer,
)
from .pagination import RecipePagination, SubscriptionPagination


class UserViewSet(djoser_views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    http_method_names = ["get", "post", "put", "delete"]

    def get_permissions(self):
        if self.action in ["create", "list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[AllowAny],
    )
    def me(self, request):
        if request.user.is_authenticated:
            user = request.user
            serializer = UserSerializer(user, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Пользователь не аутентифицирован."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def update_avatar(self, request):
        user = request.user

        if request.method == "PUT":
            if "avatar" in request.data:
                format, imgstr = request.data["avatar"].split(";base64,")
                ext = format.split("/")[-1]

                avatar_file = ContentFile(
                    base64.b64decode(imgstr), name=f"avatar_{user.id}.{ext}"
                )

                user.avatar.save(avatar_file.name, avatar_file)
                user.save()

                avatar_url = request.build_absolute_uri(user.avatar.url)

                return Response(
                    {"avatar": avatar_url}, status=status.HTTP_200_OK
                )

        elif request.method == "DELETE":
            user.avatar.delete(save=True)

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"detail": "No avatar provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post", "delete"])
    def subscribe(self, request, id=None):
        user = request.user
        author = self.get_object()

        if user == author:
            return Response(
                {"detail": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"detail": "Вы уже подписаны на этого автора."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Subscription.objects.create(user=user, author=author)
            serializer = UserSerializer(author, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            subscription = Subscription.objects.filter(
                user=user, author=author
            ).first()
            if not subscription:
                return Response(
                    {"detail": "Вы не подписаны на этого автора."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription.delete()
            return Response(
                {"detail": "Вы успешно отписались от автора."},
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(
        detail=False, methods=["get"], pagination_class=SubscriptionPagination
    )
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(
            user=request.user
        ).order_by("id")
        page = self.paginate_queryset(subscriptions)

        if page is not None:
            serializer = UserSerializer(
                [subscription.author for subscription in page],
                many=True,
                context={"request": request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserSerializer(
            [subscription.author for subscription in subscriptions],
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    http_method_names = [
        "get",
    ]
    filter_backends = (filters.SearchFilter,)
    search_fields = ["name"]

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get("name", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by("id")
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    http_method_names = [
        "get",
    ]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by("name")
    serializer_class = RecipeSerializer
    pagination_class = RecipePagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = ["author"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_recipe_favorited=Exists(
                    Favorite.objects.filter(author=user, recipe=OuterRef("pk"))
                ),
                is_in_user_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        author=user, recipe=OuterRef("pk")
                    )
                ),
            )
        else:
            queryset = queryset.annotate(
                is_recipe_favorited=Value(
                    False, output_field=models.BooleanField()
                ),
                is_in_user_shopping_cart=Value(
                    False, output_field=models.BooleanField()
                ),
            )

        is_favorited = self.request.query_params.get("is_favorited", None)
        if is_favorited is not None:
            if user.is_authenticated:
                if is_favorited.lower() == "true":
                    queryset = queryset.filter(favorites__author=user)
                elif is_favorited.lower() == "false":
                    queryset = queryset.exclude(favorites__author=user)
        if self.request.query_params.get("is_favorited") in ["1", "true"]:
            queryset = queryset.filter(is_recipe_favorited=True)

        if self.request.query_params.get("is_in_shopping_cart") in [
            "1",
            "true",
        ]:
            queryset = queryset.filter(is_in_user_shopping_cart=True)

        tag_slugs = self.request.query_params.getlist("tags")
        if tag_slugs:
            queryset = queryset.filter(tags__slug__in=tag_slugs).distinct()

        return queryset

    def destroy(self, request, pk=None):
        try:
            recipe = self.get_object()
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Рецепт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Необходима аутентификация."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if recipe.author != request.user:
            raise PermissionDenied("Вы не можете удалить чужой рецепт.")

        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], url_path="favorite")
    def toggle_favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"detail": "Необходима аутентификация."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        favorite = Favorite.objects.filter(author=user, recipe=recipe).first()

        if request.method == "DELETE":
            if not favorite:
                return Response(
                    {"detail": "Рецепт не добавлен в избранное."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if favorite:
            return Response(
                {"detail": "Рецепт уже в избранном."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Favorite.objects.create(author=user, recipe=recipe)
        serializer = RecipeSerializer(recipe, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="download_shopping_cart")
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(author=request.user)

        if not shopping_cart.exists():
            return Response(
                {"detail": "Shopping cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ingredients_summary = {}

        for item in shopping_cart:
            recipe_ingredients = item.recipe.recipe_ingredients.all()

            for ingredient in recipe_ingredients:
                ingredient_name = ingredient.ingredient.name
                ingredient_unit = ingredient.ingredient.measurement_unit
                ingredient_amount = ingredient.amount

                if ingredient_name in ingredients_summary:
                    ingredients_summary[ingredient_name][
                        "amount"
                    ] += ingredient_amount
                else:
                    ingredients_summary[ingredient_name] = {
                        "amount": ingredient_amount,
                        "unit": ingredient_unit,
                    }

        content = "Ваш список покупок:\n"
        for ingredient, data in ingredients_summary.items():
            content += f"{ingredient}: {data['amount']} {data['unit']}\n"

        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"detail": "Необходима аутентификация."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if request.method == "POST":
            if ShoppingCart.objects.filter(
                author=user, recipe=recipe
            ).exists():
                return Response(
                    {"detail": "Этот рецепт уже в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ShoppingCart.objects.create(author=user, recipe=recipe)
            response_data = {
                "id": recipe.id,
                "name": recipe.name,
                "image": request.build_absolute_uri(recipe.image.url),
                "cooking_time": recipe.cooking_time,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            shopping_cart_item = ShoppingCart.objects.filter(
                author=user, recipe=recipe
            ).first()
            if not shopping_cart_item:
                return Response(
                    {"detail": "Этот рецепт не был в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            shopping_cart_item.delete()
            return Response(
                {"detail": "Рецепт удален из списка покупок."},
                status=status.HTTP_204_NO_CONTENT,
            )

    def generate_short_code(self):
        return "".join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_recipe_link(self, request, pk=None):
        recipe = self.get_object()

        short_link, created = ShortLink.objects.get_or_create(recipe=recipe)

        if created:
            short_link.short_code = self.generate_short_code()
            short_link.save()

        short_url = f"https://{settings.SITE_DOMAIN}/s/{short_link.short_code}"

        return Response({"short-link": short_url}, status=status.HTTP_200_OK)


def redirect_to_recipe(request, short_code):
    print(f"Redirecting short_code: {short_code}")
    short_link = get_object_or_404(ShortLink, short_code=short_code)

    recipe_url = reverse("recipes-detail", kwargs={"pk": short_link.recipe.id})
    print(f"Redirecting to recipe URL: {recipe_url}")

    return redirect(recipe_url)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "delete"]

    def get_queryset(self):
        user = self.request.user
        favorite_ids = Favorite.objects.filter(author=user).values_list(
            "recipe_id", flat=True
        )
        return Recipe.objects.filter(id__in=favorite_ids)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return Recipe.objects.filter(
            in_shopping_cart__author=self.request.user
        )

    def list(self, request, *args, **kwargs):
        recipes = self.get_queryset()
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)
