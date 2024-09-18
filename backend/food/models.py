from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class Ingredient(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=16
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=64,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Идентификатор',
        max_length=64,
        unique=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'slug'],
                name='unique_tag'
            )
        ]

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=256
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления'
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
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
    def __str__(self):
        return self.name




class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]
        verbose_name = 'Рецепты и Ингредиенты'
        verbose_name_plural = 'Рецепты и Ингредиенты'
    
    def __str__(self):
        return f'{self.ingredient.name} ({self.amount})'




class Purchase(models.Model):
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

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'



class Favorite(models.Model):
    author = models.ForeignKey(
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
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'recipe'],
                name='author_recipe'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class Subscription(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    subscribed_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='subcribers',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=128,
        unique=True,
        help_text=(
            f'Адрес электронной почты, не более 128 символов'
        ),
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=64,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name='Имя Отчество',
        max_length=128,
        blank=True,
        null=True,
        help_text=(
            f'Имя Отчество, не более 128 символов'
        ),
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=128,
        blank=True,
        null=True,
        help_text=(
            f'Фамилия, не более 128 символов'
        ),
    )
    is_subscribed = models.BooleanField(
        default=False,
        verbose_name='Подписка'
    )
    avatar = models.URLField(
        verbose_name='Аватар',
        max_length=200,
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'  # Аутентификация через email
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username