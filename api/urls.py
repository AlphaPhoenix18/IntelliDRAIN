from django.urls import path
from .views import BlockageDetectionView

urlpatterns = [
    path('detect/', BlockageDetectionView.as_view(), name='blockage-detection'),
]
