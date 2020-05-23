from django.urls import path
from . import views

urlpatterns = [
    path('decode/', views.DecodeAPIView.as_view(), name='decode'),
    path('encode/', views.EncodeAPIView.as_view(), name='encode'),
]
