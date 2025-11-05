# In odc-api/core/serializers.py (CORRECTED)

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import (
    Cook, ServiceArea, AvailabilitySlot,
    Ingredient, Dish, DishIngredient, ScheduledTask, Wallet
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
    # Correctly sources the balance from the related Wallet model
    wallet_balance = serializers.DecimalField(source='wallet.balance', read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = Cook
        # Removed 'years_of_experience' to match the simplified signup form
        fields = ['id', 'user', 'full_name', 'phone_number', 'password', 'has_set_availability', 'wallet_balance']
        read_only_fields = ['user', 'has_set_availability','wallet_balance']

    def create(self, validated_data):
        # This logic correctly creates a User and a linked Cook profile
        user = User.objects.create_user(
            username=validated_data['phone_number'], 
            password=validated_data.pop('password')
        )
        cook = Cook.objects.create(user=user, **validated_data)
        return cook

class ScheduledTaskSerializer(serializers.ModelSerializer):
    # This now correctly nests the full Dish object, which is what the frontend expects
    dish = DishSerializer(read_only=True)
    
    class Meta:
        model = ScheduledTask
        # The incorrect 'dish_name' field is removed and replaced by 'dish'
        fields = ['id', 'dish', 'date', 'start_time', 'estimated_duration_minutes', 'status', 'cook_earnings']