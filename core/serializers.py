from django.contrib.auth.models import User
from rest_framework import serializers
from .models import (
    Cook, ServiceArea, AvailabilitySlot,
    Ingredient, Dish, DishIngredient, ScheduledTask
)

# ==============================================================================
#  Dish & Ingredient Serializers
# ==============================================================================

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name']

class DishIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    class Meta:
        model = DishIngredient
        fields = ['ingredient', 'ingredient_name', 'quantity', 'unit', 'is_must_have']

class DishSerializer(serializers.ModelSerializer):
    ingredients = DishIngredientSerializer(source='dishingredient_set', many=True, read_only=True)
    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'description', 'ingredients',
            'video_url', 'time_to_cook_minutes', 'recipe_steps',
            'special_instructions', 'required_utensils'
        ]
# ==============================================================================
#  Cook, Area & Availability Serializers
# ==============================================================================

class ServiceAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceArea
        fields = ['id', 'pincode', 'city', 'name']

class AvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = ['id', 'cook', 'day_of_week', 'start_time', 'end_time']

class CookSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = Cook
        fields = ['id', 'user', 'full_name', 'phone_number', 'years_of_experience', 'password', 'has_set_availability']
        read_only_fields = ['user', 'has_set_availability']
    def create(self, validated_data):
        user = User.objects.create_user(username=validated_data['phone_number'], password=validated_data.pop('password'))
        cook = Cook.objects.create(user=user, **validated_data)
        return cook

# ... (Add this serializer near the end of the file)
class ScheduledTaskSerializer(serializers.ModelSerializer):
    dish = DishSerializer(read_only=True)
    class Meta:
        model = ScheduledTask
        fields = ['id', 'dish', 'dish_name', 'date', 'start_time', 'estimated_duration_minutes', 'status', 'cook_earnings']