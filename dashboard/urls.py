from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DRF Router für Bautechnik API
router = DefaultRouter()
router.register(r'api/material', views.MaterialViewSet, basename='material')
router.register(r'api/material-schicht', views.MaterialSchichtViewSet, basename='material-schicht')
router.register(r'api/konstruktion', views.KonstruktionViewSet, basename='konstruktion')
router.register(r'api/konstruktion-schicht', views.KonstruktionSchichtViewSet, basename='konstruktion-schicht')
router.register(r'api/fenster-typ', views.FensterTypViewSet, basename='fenster-typ')
router.register(r'api/tür-typ', views.TürTypViewSet, basename='tür-typ')
router.register(r'api/sonnenschutz-typ', views.SonnenschutzTypViewSet, basename='sonnenschutz-typ')
router.register(r'api/gebäude', views.GebäudeViewSet, basename='gebäude')
router.register(r'api/bauteil', views.BauteilViewSet, basename='bauteil')
router.register(r'api/ekobaudat-material', views.EkobaudatMaterialViewSet, basename='ekobaudat-material')

urlpatterns = [
    path("", views.index),
    path("calculate/", views.calculate),
    path("calculate-system/", views.calculate_system),
    path("calculate-pv/", views.calculate_pv),
    path("calculate-balance/", views.calculate_balance),
    path("upload-ekobaudat-csv/", views.upload_ekobaudat_csv, name="upload-ekobaudat-csv"),
    
    # REST API Routes
    path("", include(router.urls)),
]