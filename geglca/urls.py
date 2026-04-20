from django.contrib import admin
from django.urls import path, include

urlpatterns = [
<<<<<<< HEAD
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
]
=======
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
]
>>>>>>> 60c4f5d9d2418ec8b81cc3bb4796449a779cf8a0
