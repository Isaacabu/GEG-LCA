from django.urls import path
from .views import index, calculate_heat_loss

urlpatterns = [
    path("", index),
    path("calculate/", calculate_heat_loss),
]
