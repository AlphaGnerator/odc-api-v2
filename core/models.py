# In odc-api/core/models.py (FINAL, CORRECTED VERSION)

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# ==============================================================================
#  Dish & Ingredient Models
# ==============================================================================
class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Dish(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    
    # --- NEW FIELDS ---
    video_url = models.URLField(max_length=512, blank=True)
    time_to_cook_minutes = models.PositiveSmallIntegerField(default=30)
    recipe_steps = models.TextField(blank=True) # For step-by-step instructions
    special_instructions = models.TextField(blank=True)
    required_utensils = models.CharField(max_length=255, blank=True)
    # ------------------

    ingredients = models.ManyToManyField(Ingredient, through='DishIngredient', blank=True)

    def __str__(self):
        return self.name

class DishIngredient(models.Model):
    class Unit(models.TextChoices):
        GRAMS = 'g', 'Grams'; ML = 'ml', 'Milliliters'; PIECES = 'pcs', 'Pieces';
        TSP = 'tsp', 'Teaspoon'; TBSP = 'tbsp', 'Tablespoon'; UNIT = 'unit', 'Unit'
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=7, decimal_places=2)
    unit = models.CharField(max_length=5, choices=Unit.choices)
    is_must_have = models.BooleanField(default=True)
    def __str__(self): return f"{self.dish.name} - {self.quantity}{self.unit} of {self.ingredient.name}"

# ==============================================================================
#  Cook & Availability Models
# ==============================================================================
class ServiceArea(models.Model):
    pincode = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=50)
    name = models.CharField(max_length=100, blank=True)
    def __str__(self): return f"{self.pincode} ({self.name}, {self.city})"

class Cook(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cook_profile")
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)
    has_set_availability = models.BooleanField(default=False) # <-- ADD THIS
    availability_last_updated = models.DateTimeField(null=True, blank=True) #
    years_of_experience = models.PositiveSmallIntegerField(default=0)
    onboarding_quiz_score = models.PositiveSmallIntegerField(default=0)
    cooking_test_score = models.PositiveSmallIntegerField(default=0)
    overall_competence_score = models.FloatField(default=0.0)
    
    class KYCStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'
        
    kyc_status = models.CharField(max_length=20, choices=KYCStatus.choices, default=KYCStatus.PENDING)
    kyc_document_url = models.CharField(max_length=512, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    service_areas = models.ManyToManyField('ServiceArea', blank=True)
    certified_dishes = models.ManyToManyField('Dish', blank=True)
    
    def save(self, *args, **kwargs):
        self.overall_competence_score = (self.onboarding_quiz_score * 0.4) + (self.cooking_test_score * 0.6)
        super().save(*args, **kwargs)
        
    def __str__(self): return f"{self.full_name} ({self.phone_number})"

class AvailabilitySlot(models.Model):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, 'Monday'; TUESDAY = 1, 'Tuesday'; WEDNESDAY = 2, 'Wednesday';
        THURSDAY = 3, 'Thursday'; FRIDAY = 4, 'Friday'; SATURDAY = 5, 'Saturday';
        SUNDAY = 6, 'Sunday'
    
    cook = models.ForeignKey(Cook, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    def __str__(self): return f"{self.cook.full_name} - {self.get_day_of_week_display()}"

class ScheduledTask(models.Model):
    cook = models.ForeignKey(Cook, on_delete=models.CASCADE, related_name='scheduled_tasks')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    estimated_duration_minutes = models.PositiveSmallIntegerField(default=60)
    
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'; IN_PROGRESS = 'IN_PROGRESS', 'In Progress';
        COMPLETED = 'COMPLETED', 'Completed'; CANCELLED = 'CANCELLED', 'Cancelled'
        
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    cook_earnings = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
            return f"{self.cook.full_name} - {self.dish.name} on {self.date}"