from django.urls import path
from . import views

urlpatterns = [
<<<<<<< HEAD
    path("", views.index),
    path("calculate/", views.calculate),
    path("calculate-system/", views.calculate_system),
]
=======
    path('', views.index),
    path('calculate/', views.calculate),
]
>>>>>>> 60c4f5d9d2418ec8b81cc3bb4796449a779cf8a0
