# In odc-api/core/views.py (FINAL, ROBUST VERSION)

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Sum, F
from django.utils import timezone
import os, datetime
from google.cloud import storage
from .models import *
from .serializers import *

# ==============================================================================
#  API Endpoints
# ==============================================================================

@api_view(['GET'])
def health(request):
    """A simple endpoint to check if the API is running."""
    return Response({'status': 'ok', 'message': 'API is running!'})

# --- Model ViewSets ---

class CookViewSet(viewsets.ModelViewSet):
    queryset = Cook.objects.all().order_by('-created_at')
    serializer_class = CookSerializer

class ServiceAreaViewSet(viewsets.ModelViewSet):
    queryset = ServiceArea.objects.all()
    serializer_class = ServiceAreaSerializer

class AvailabilitySlotViewSet(viewsets.ModelViewSet):
    queryset = AvailabilitySlot.objects.all()
    serializer_class = AvailabilitySlotSerializer

class DishViewSet(viewsets.ModelViewSet):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

class ScheduledTaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduledTaskSerializer
    def get_queryset(self):
        if hasattr(self.request.user, 'cook_profile'):
            return ScheduledTask.objects.filter(cook=self.request.user.cook_profile)
        return ScheduledTask.objects.none()

# --- Custom API Views ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cook_dashboard_summary(request):
    """
    Provides a consolidated summary for the logged-in cook.
    This version is robust and handles cases where a wallet might not exist.
    """
    try:
        cook_profile = request.user.cook_profile
    except Cook.DoesNotExist:
        return Response({"error": "This user is not a cook."}, status=status.HTTP_404_NOT_FOUND)

    today = timezone.now().date()
    
    # Safely get wallet balance
    try:
        wallet_balance = cook_profile.wallet.balance
    except Wallet.DoesNotExist:
        wallet_balance = 0.00

    todays_earnings = ScheduledTask.objects.filter(
        cook=cook_profile, 
        status=ScheduledTask.Status.COMPLETED,
        date=today
    ).aggregate(total=Sum('cook_earnings'))['total'] or 0.00
    
    upcoming_tasks = ScheduledTask.objects.filter(
        cook=cook_profile, 
        date__gte=today, 
        status=ScheduledTask.Status.SCHEDULED
    ).order_by('date', 'start_time')
    
    return Response({
        'wallet_balance': wallet_balance,
        'todays_earnings': todays_earnings,
        'upcoming_schedule': ScheduledTaskSerializer(upcoming_tasks, many=True).data,
        'cook_name': cook_profile.full_name or request.user.username,
        # Also include the availability status for routing
        'has_set_availability': cook_profile.has_set_availability 
    })

class CookAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        try:
            cook_profile = request.user.cook_profile
        except Cook.DoesNotExist:
            return Response({"error": "Cook profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        slots_data = request.data.get('slots')
        if not isinstance(slots_data, list):
            return Response({"error": "Invalid 'slots' data format."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            AvailabilitySlot.objects.filter(cook=cook_profile).delete()
            for slot_data in slots_data:
                AvailabilitySlot.objects.create(cook=cook_profile, **slot_data)
            
            cook_profile.has_set_availability = True
            cook_profile.save()
            return Response({"status": "success"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenerateUploadUrlView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        bucket_name = os.environ.get('GCS_BUCKET_NAME')
        file_name = request.data.get('file_name')
        if not bucket_name or not file_name:
            return Response({"error": "Server not configured for uploads or file_name missing."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        storage_client = storage.Client()
        blob = storage_client.bucket(bucket_name).blob(file_name)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="PUT",
        )
        return Response({"signed_url": url})