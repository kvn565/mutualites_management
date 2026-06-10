from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import MutualiteViewSet, DashboardAPIView

router = DefaultRouter()
router.register(r'mutualites', MutualiteViewSet, basename='api-mutualite')

app_name = 'superadmin-api'

urlpatterns = [
    path('', include(router.urls)),
    path('tableau-de-bord/', DashboardAPIView.as_view(), name='api-dashboard'),
]
