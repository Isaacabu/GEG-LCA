from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path("calculate/", views.calculate),
    path("calculate-system/", views.calculate_system),
]