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
    """
    The main serializer for the Cook model. This is the most complex one
    because it handles the creation of a related User account.
    """
    # --- WRITE-ONLY fields for creating/updating related objects ---
    # These fields are used for input (when you POST or PATCH) but are not
    # displayed on output (when you GET).

    # For creating a User account
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'} # Hides the text in the browsable API form
    )

    # For linking ServiceAreas and certified Dishes by their IDs
    service_area_ids = serializers.PrimaryKeyRelatedField(
        queryset=ServiceArea.objects.all(), many=True, write_only=True, source='service_areas', required=False
    )
    certified_dish_ids = serializers.PrimaryKeyRelatedField(
        queryset=Dish.objects.all(), many=True, write_only=True, source='certified_dishes', required=False
    )

    # --- READ-ONLY fields for displaying related objects ---
    # These fields are used for output (GET) but not for input. They show the
    # full details of the related objects, not just their IDs.
    service_areas = ServiceAreaSerializer(many=True, read_only=True)
    certified_dishes = DishSerializer(many=True, read_only=True)

    class Meta:
        model = Cook
        # List all the fields from the Cook model that we want to expose
        fields = [
            'id',
            'user', # We can now show the user ID
            'full_name',
            'phone_number',
            'years_of_experience',
            'onboarding_quiz_score',
            'cooking_test_score',
            'overall_competence_score',
            'kyc_status',
            'kyc_document_url',
            'is_active',
            'created_at',
            
            # Add all the write-only and read-only fields
            'username',
            'password',
            'service_area_ids',
            'certified_dish_ids',
            'service_areas',
            'certified_dishes',
        ]
        # These fields will be calculated automatically or set by the system,
        # so we make them read-only.
        read_only_fields = [
            'user',
            'overall_competence_score',
            'created_at',
            'service_areas',
            'certified_dishes',
        ]

    def create(self, validated_data):
        """
        This special method overrides the default create behavior. It allows us
        to handle the creation of the User and the Cook profile in one API call.
        """
        # Pop the user-related data from the dictionary
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        
        # Pop the ManyToMany data, if it exists, to handle it separately
        service_areas_data = validated_data.pop('service_areas', [])
        certified_dishes_data = validated_data.pop('certified_dishes', [])

        # Step 1: Create the built-in Django User
        user = User.objects.create_user(
            username=username,
            password=password
        )
        
        # Step 2: Create the Cook profile, linking it to the user
        cook_profile = Cook.objects.create(user=user, **validated_data)
        
        # Step 3: Set the ManyToMany relationships
        if service_areas_data:
            cook_profile.service_areas.set(service_areas_data)
        if certified_dishes_data:
            cook_profile.certified_dishes.set(certified_dishes_data)
            
        return cook_profile
# In odc-api/core/serializers.py

# ... (Add this serializer near the end of the file)
class ScheduledTaskSerializer(serializers.ModelSerializer):
    dish = DishSerializer(read_only=True)
    class Meta:
        model = ScheduledTask
        fields = ['id', 'dish', 'dish_name', 'date', 'start_time', 'estimated_duration_minutes', 'status', 'cook_earnings']