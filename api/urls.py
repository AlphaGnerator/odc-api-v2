# In odc-api/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core import views
from rest_framework_simplejwt.views import TokenObtainPairView

router = DefaultRouter()
router.register(r'cooks', views.CookViewSet); router.register(r'service-areas', views.ServiceAreaViewSet)
router.register(r'availability-slots', views.AvailabilitySlotViewSet); router.register(r'dishes', views.DishViewSet)
router.register(r'ingredients', views.IngredientViewSet); router.register(r'tasks', views.ScheduledTaskViewSet, basename='task')

urlpatterns = [
    path('health', views.health),
    path('api/auth/login/', TokenObtainPairView.as_view()),
    path('api/cook-dashboard/', views.cook_dashboard_summary),
    path('api/cook/availability/', views.CookAvailabilityView.as_view()),
    path('api/', include(router.urls)),
]