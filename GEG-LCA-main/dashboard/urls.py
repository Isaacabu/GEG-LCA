from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path("calculate/", views.calculate),
    path("calculate-system/", views.calculate_system),
    path("projects/save/", views.save_project),
    path("projects/<uuid:project_id>/", views.load_project),
    path("projects/<uuid:project_id>/report/", views.project_report),
]