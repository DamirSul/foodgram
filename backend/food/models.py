from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class Ingredient(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        verbose_name='Система счисления',
        max_length=16
    )

    class Meta:
        pass

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=64
    )
    slug = models.SlugField(
        verbose_name='Идентификатор',
        max_length=64,
        unique=True
    )

    class Meta:
        pass

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=256
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Времяя приготовленияя'
    )
    image = models.ImageField(verbose_name='Фотография')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Список ингредиентов'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )

    class Meta:
        pass

    def __str__(self):
        return self.name




class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент")
    amount = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f"{self.amount} {self.ingredient.name} для {self.recipe.name}"



class Purchases(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=124,

    )
    image = models.ImageField(
        verbose_name='Фотография'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления'
    )



class Favorites(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('user', 'recipe')



class Subscriptions(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    subscribed_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='subcribers',
        on_delete=models.CASCADE
    )


class CustomUser(AbstractUser):
    is_subscribed = models.BooleanField(default=False)
    avatar = models.URLField(max_length=200, blank=True, null=True)

    class Meta:
        pass

    def __str__(self):
        return self.username