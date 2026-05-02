from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Material, MaterialSchicht, Konstruktion, KonstruktionSchicht,
    FensterTyp, TürTyp, SonnenschutzTyp, Gebäude, Bauteil
)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'rohdichte', 'lambda_value', 'c_specific', 'mu_value']
    list_filter = ['rohdichte', 'lambda_value']
    search_fields = ['name', 'description']
    fieldsets = (
        ('Grunddaten', {'fields': ('name', 'description')}),
        ('Thermische Eigenschaften', {'fields': ('rohdichte', 'lambda_value', 'c_specific', 'mu_value')}),
    )


@admin.register(MaterialSchicht)
class MaterialSchichtAdmin(admin.ModelAdmin):
    list_display = ['material', 'thickness_mm', 'r_value_display']
    list_filter = ['material__rohdichte']
    
    def r_value_display(self, obj):
        return f"{obj.r_value:.4f} m²K/W"
    r_value_display.short_description = "R-Wert"


class KonstruktionSchichtInline(admin.TabularInline):
    model = KonstruktionSchicht
    extra = 1
    fields = ['order', 'schicht', 'material_lambda', 'material_ro']
    readonly_fields = ['material_lambda', 'material_ro']
    
    def material_lambda(self, obj):
        return f"λ={obj.schicht.material.lambda_value}" if obj.schicht else "-"
    material_lambda.short_description = "λ (W/mK)"
    
    def material_ro(self, obj):
        return f"ρ={obj.schicht.material.rohdichte}" if obj.schicht else "-"
    material_ro.short_description = "ρ (kg/m³)"


@admin.register(Konstruktion)
class KonstruktionAdmin(admin.ModelAdmin):
    list_display = ['name', 'typ', 'u_value_display', 'r_value_display']
    list_filter = ['typ']
    search_fields = ['name']
    inlines = [KonstruktionSchichtInline]
    fieldsets = (
        ('Grunddaten', {'fields': ('name', 'typ', 'description')}),
        ('Wärmeübergänge', {'fields': ('r_si', 'r_se')}),
    )
    
    def u_value_display(self, obj):
        return f"{obj.u_value:.3f} W/m²K"
    u_value_display.short_description = "U-Wert"
    
    def r_value_display(self, obj):
        return f"{obj.r_value_total:.3f} m²K/W"
    r_value_display.short_description = "R-Wert gesamt"


@admin.register(FensterTyp)
class FensterTypAdmin(admin.ModelAdmin):
    list_display = ['name', 'u_w', 'g_value', 'psi_edge']
    search_fields = ['name']
    fieldsets = (
        ('Grunddaten', {'fields': ('name', 'description')}),
        ('Eigenschaften', {'fields': ('u_w', 'g_value', 'psi_edge')}),
    )


@admin.register(TürTyp)
class TürTypAdmin(admin.ModelAdmin):
    list_display = ['name', 'u_value', 'luftdichtheit']
    search_fields = ['name']


@admin.register(SonnenschutzTyp)
class SonnenschutzTypAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'typ', 'reduktionsfaktor']
    list_filter = ['position', 'typ']
    search_fields = ['name']


class BauteilInline(admin.TabularInline):
    model = Bauteil
    extra = 1
    fields = ['name', 'orientierung', 'fläche', 'konstruktion', 'fenster_typ', 'fenster_fläche']


@admin.register(Gebäude)
class GebäudeAdmin(admin.ModelAdmin):
    list_display = ['name', 'standort', 'bgf', 'gradstunden']
    search_fields = ['name', 'standort']
    inlines = [BauteilInline]
    fieldsets = (
        ('Grunddaten', {'fields': ('name', 'standort')}),
        ('Geometrie', {'fields': ('bgf',)}),
        ('Klimadaten', {'fields': ('gradstunden',)}),
    )


@admin.register(Bauteil)
class BauteilAdmin(admin.ModelAdmin):
    list_display = ['name', 'gebäude', 'orientierung', 'fläche', 'transmissionsverlust_display']
    list_filter = ['orientierung', 'gebäude']
    search_fields = ['name', 'gebäude__name']
    fieldsets = (
        ('Grunddaten', {'fields': ('gebäude', 'name', 'orientierung')}),
        ('Flächen', {'fields': ('fläche', 'fenster_fläche')}),
        ('Zuordnungen', {'fields': ('konstruktion', 'fenster_typ', 'sonnenschutz')}),
    )
    
    def transmissionsverlust_display(self, obj):
        return f"{obj.transmissionsverlust:.2f} W/K"
    transmissionsverlust_display.short_description = "H (W/K)"
