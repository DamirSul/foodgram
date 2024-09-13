from rest_framework import serializers, status, validators
from rest_framework.relations import SlugRelatedField
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from food.models import *


User = get_user_model()
