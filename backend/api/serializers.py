import base64

from django.db import transaction
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from food.models import (
    Ingredient,
    Tag,
    Recipe,
    Subscription,
    Favorite,
    ShoppingCart,
    RecipeIngredient,
)
from users.models import User


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if not data:
            return super().to_internal_value(data)

        if isinstance(data, str):
            if data.startswith("data:image"):
                format, imgstr = data.split(";base64,")
                ext = format.split("/")[-1]
                data = ContentFile(
                    base64.b64decode(imgstr), name=f"temp.{ext}"
                )

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")

    class Meta:
        model = RecipeIngredient
        fields = ["id", "amount"]


class AuthorSerializerNew(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
            "avatar",
        ]

    def get_avatar(self, obj):
        return obj.avatar.url if obj.avatar else None


class IngredientSerializerNew(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "measurement_unit", "amount"]


class FavoriteRecipeSerializerNew(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]

    def to_representation(self, instance):
        request = self.context.get("request")
        return {
            "id": instance.id,
            "name": instance.name,
            "image": (
                request.build_absolute_uri(instance.image.url)
                if instance.image
                else None
            ),
            "cooking_time": instance.cooking_time,
        }


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        many=True, source="recipe_ingredients"
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), write_only=True
    )
    image = Base64ImageField(required=True)
    author = serializers.ReadOnlyField(source="author.username")
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "text",
            "cooking_time",
            "ingredients",
            "tags",
            "image",
            "is_favorited",
            "is_in_shopping_cart",
            "author",
        ]

    def to_representation(self, instance):
        request = self.context.get("request")

        if request and "favorite" in request.path:
            return FavoriteRecipeSerializerNew(
                instance, context=self.context
            ).data

        representation = super().to_representation(instance)
        representation["tags"] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        representation["author"] = AuthorSerializerNew(
            instance.author
        ).data
        representation["ingredients"] = IngredientSerializerNew(
            instance.recipe_ingredients.all(), many=True
        ).data
        return representation

    def create_recipe_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(
                    id=ingredient_data["ingredient"]["id"]
                ),
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                "Поле ingredients не может быть пустым."
            )

        ingredient_ids = []
        for ingredient_data in ingredients:
            if ingredient_data["amount"] < 1:
                raise serializers.ValidationError(
                    "Количество ингредиента должно быть больше 0."
                )
            if ingredient_data["ingredient"]["id"] in ingredient_ids:
                raise serializers.ValidationError(
                    "Ингредиенты не должны повторяться."
                )
            ingredient_ids.append(ingredient_data["ingredient"]["id"])

            try:
                Ingredient.objects.get(
                    id=ingredient_data["ingredient"]["id"]
                )
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    "Ингредиент с таким ID не найден."
                )

        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                "Поле tags не может быть пустым."
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                "Теги не должны повторяться."
            )
        return tags

    def validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError(
                "Время готовки должно быть больше 0."
            )
        return cooking_time

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients")
        tags_data = validated_data.pop("tags", [])

        recipe = Recipe.objects.create(**validated_data)
        self.create_recipe_ingredients(recipe, ingredients_data)
        recipe.tags.set(tags_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        tags_data = validated_data.pop("tags", [])

        if not ingredients_data:
            raise serializers.ValidationError(
                "Поле ingredients не может быть пустым."
            )
        if not tags_data:
            raise serializers.ValidationError(
                "Поле tags не может быть пустым."
            )

        instance = super().update(instance, validated_data)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_recipe_ingredients(instance, ingredients_data)
        instance.tags.set(tags_data)

        return instance

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                author=request.user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                author=request.user, recipe=obj
            ).exists()
        return False

    def validate(self, data):
        request = self.context.get("request")
        if (
            request.method in ["PUT", "PATCH"]
            and request.user != self.instance.author
        ):
            raise PermissionDenied(
                "Вы не можете редактировать чужой рецепт."
            )
        return data


class RecipeListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            return request.build_absolute_uri(obj.avatar.url)
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        request = self.context.get("request")

        if request and (
            "subscriptions" in request.path
            or "subscribe" in request.path
        ):
            recipes = Recipe.objects.filter(author=instance)
            recipes_limit = request.query_params.get(
                "recipes_limit", None
            )
            if recipes_limit is not None:
                try:
                    recipes_limit = int(recipes_limit)
                    recipes = recipes[:recipes_limit]
                except ValueError:
                    pass
            representation["recipes"] = RecipeListSerializer(
                recipes, many=True, context=self.context
            ).data
            representation["recipes_count"] = recipes.count()

        return representation


class SubscriptionSerializer(serializers.ModelSerializer):
    recipe_count = serializers.SerializerMethodField()
    recipes = RecipeSerializer(many=True)
    user = serializers.StringRelatedField()

    class Meta:
        model = Subscription
        fields = ["user", "recipes", "recipe_count"]

    def get_recipe_count(self, obj):
        return obj.recipes.count()


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "recipe"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["tags"] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        representation["author"] = AuthorSerializerNew(
            instance.author
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer()

    class Meta:
        model = ShoppingCart
        fields = ("recipe",)


class SimpleRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]
