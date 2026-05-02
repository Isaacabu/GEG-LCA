from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path("calculate/", views.calculate),
    path("calculate-system/", views.calculate_system),
    path("materials/list/", views.materials_list),
    path("materials/create/", views.create_material),
    path("materials/import/", views.import_materials),
]
