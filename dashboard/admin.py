from django.contrib import admin
from .models import EkobaudatMaterial


@admin.register(EkobaudatMaterial)
class EkobaudatMaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "category", "u_value", "embodied_co2")
    search_fields = ("name", "producer", "category")
    list_filter = ("category",)
