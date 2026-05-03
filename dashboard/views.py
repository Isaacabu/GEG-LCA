import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Importiere zentrale Hilfsfunktionen und Konstanten
from .utils import safe_float, validate_non_negative, validate_u_value, get_rating
from .csv_utils import import_materials_from_uploaded_file
from .constants import (
    SOLAR_FACTORS, PRIMARY_ENERGY_FACTORS, CO2_FACTORS,
    RATING_THRESHOLDS, SYSTEM_RATING_THRESHOLDS,
    DEFAULT_GRADSTUNDEN, DEFAULT_G_VALUE, VALID_HEATING_SYSTEMS,
    DEFAULT_HOTWATER_DEMAND, DEFAULT_AUXILIARY_ELECTRICITY,
    MAX_U_VALUE, MAX_G_VALUE, MIN_G_VALUE,
    DEFAULT_EFFICIENCY, DEFAULT_COP, MAX_EFFICIENCY, MAX_COP
)


def index(request):
    return render(request, "dashboard/index.html")


@csrf_exempt
@require_POST
def upload_ekobaudat(request):
    uploaded_file = request.FILES.get("csv_file")
    if not uploaded_file:
        return JsonResponse({"ok": False, "errors": ["Keine CSV-Datei hochgeladen."]}, status=400)

    filename = (uploaded_file.name or "").lower()
    if not filename.endswith(".csv"):
        return JsonResponse({"ok": False, "errors": ["Bitte eine CSV-Datei hochladen."]}, status=400)

    try:
        result = import_materials_from_uploaded_file(uploaded_file, EkobaudatMaterial)
        return JsonResponse({
            "ok": True,
            "message": "Ökobaudat erfolgreich importiert.",
            "file": uploaded_file.name,
            **result,
        })
    except Exception as exc:
        return JsonResponse({"ok": False, "errors": [f"Import fehlgeschlagen: {exc}"]}, status=400)


@csrf_exempt
def calculate(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)

        bgf = safe_float(data.get("bgf"), 0)
        gradstunden = safe_float(data.get("gradstunden"), DEFAULT_GRADSTUNDEN)

        north_area = safe_float(data.get("north_area"))
        north_u = safe_float(data.get("north_u"))

        south_area = safe_float(data.get("south_area"))
        south_u = safe_float(data.get("south_u"))

        east_area = safe_float(data.get("east_area"))
        east_u = safe_float(data.get("east_u"))

        west_area = safe_float(data.get("west_area"))
        west_u = safe_float(data.get("west_u"))

        roof_area = safe_float(data.get("roof_area"))
        roof_u = safe_float(data.get("roof_u"))

        floor_area = safe_float(data.get("floor_area"))
        floor_u = safe_float(data.get("floor_u"))

        window_north_area = safe_float(data.get("window_north_area"))
        window_south_area = safe_float(data.get("window_south_area"))
        window_east_area = safe_float(data.get("window_east_area"))
        window_west_area = safe_float(data.get("window_west_area"))

        window_u = safe_float(data.get("window_u"))
        g_value = safe_float(data.get("g_value"), DEFAULT_G_VALUE)

        door_north_count = safe_float(data.get("door_north_count"), 0)
        door_south_count = safe_float(data.get("door_south_count"), 0)
        door_east_count = safe_float(data.get("door_east_count"), 0)
        door_west_count = safe_float(data.get("door_west_count"), 0)
        door_area_per_unit = safe_float(data.get("door_area_per_unit"), 2.0)
        door_u = safe_float(data.get("door_u"))

        errors = []

        validate_non_negative("BGF", bgf, errors)
        validate_non_negative("Gradstunden", gradstunden, errors)

        validate_non_negative("Nord Fläche", north_area, errors)
        validate_non_negative("Süd Fläche", south_area, errors)
        validate_non_negative("Ost Fläche", east_area, errors)
        validate_non_negative("West Fläche", west_area, errors)

        validate_u_value("Nord U-Wert", north_u, errors)
        validate_u_value("Süd U-Wert", south_u, errors)
        validate_u_value("Ost U-Wert", east_u, errors)
        validate_u_value("West U-Wert", west_u, errors)

        validate_non_negative("Dachfläche", roof_area, errors)
        validate_non_negative("Bodenfläche", floor_area, errors)
        validate_u_value("Dach U-Wert", roof_u, errors)
        validate_u_value("Boden U-Wert", floor_u, errors)

        validate_non_negative("Fenster Nord", window_north_area, errors)
        validate_non_negative("Fenster Süd", window_south_area, errors)
        validate_non_negative("Fenster Ost", window_east_area, errors)
        validate_non_negative("Fenster West", window_west_area, errors)
        validate_u_value("Fenster U-Wert", window_u, errors)

        if g_value < MIN_G_VALUE or g_value > MAX_G_VALUE:
            errors.append(f"g-Wert muss zwischen {MIN_G_VALUE} und {MAX_G_VALUE} liegen.")

        validate_non_negative("Türen Nord", door_north_count, errors)
        validate_non_negative("Türen Süd", door_south_count, errors)
        validate_non_negative("Türen Ost", door_east_count, errors)
        validate_non_negative("Türen West", door_west_count, errors)
        validate_non_negative("Türfläche pro Unit", door_area_per_unit, errors)
        validate_u_value("Tür U-Wert", door_u, errors)

        if bgf == 0:
            errors.append("BGF darf nicht 0 sein, da sonst kein spezifischer Wert berechnet werden kann.")

        if errors:
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        north_loss = north_area * north_u
        south_loss = south_area * south_u
        east_loss = east_area * east_u
        west_loss = west_area * west_u
        wall_total = north_loss + south_loss + east_loss + west_loss

        roof_loss = roof_area * roof_u
        floor_loss = floor_area * floor_u
        roof_floor_total = roof_loss + floor_loss

        window_north_loss = window_north_area * window_u
        window_south_loss = window_south_area * window_u
        window_east_loss = window_east_area * window_u
        window_west_loss = window_west_area * window_u
        window_total = (
            window_north_loss
            + window_south_loss
            + window_east_loss
            + window_west_loss
        )

        envelope_total = wall_total + roof_floor_total + window_total

        door_north_area = door_north_count * door_area_per_unit
        door_south_area = door_south_count * door_area_per_unit
        door_east_area = door_east_count * door_area_per_unit
        door_west_area = door_west_count * door_area_per_unit

        door_north_loss = door_north_area * door_u
        door_south_loss = door_south_area * door_u
        door_east_loss = door_east_area * door_u
        door_west_loss = door_west_area * door_u
        door_total = (
            door_north_loss
            + door_south_loss
            + door_east_loss
            + door_west_loss
        )

        envelope_total = envelope_total + door_total

        solar_gain_kwh = (
            window_north_area * g_value * SOLAR_FACTORS['north']
            + window_south_area * g_value * SOLAR_FACTORS['south']
            + window_east_area * g_value * SOLAR_FACTORS['east']
            + window_west_area * g_value * SOLAR_FACTORS['west']
        )

        annual_heat_demand_kwh = (envelope_total * gradstunden) / 1000
        adjusted_heat_demand_kwh = max(annual_heat_demand_kwh - solar_gain_kwh, 0)
        specific_heat_demand = adjusted_heat_demand_kwh / bgf

        rating = get_rating(specific_heat_demand)

        return JsonResponse({
            "ok": True,
            "north_loss": round(north_loss, 2),
            "south_loss": round(south_loss, 2),
            "east_loss": round(east_loss, 2),
            "west_loss": round(west_loss, 2),
            "wall_total": round(wall_total, 2),

            "roof_loss": round(roof_loss, 2),
            "floor_loss": round(floor_loss, 2),
            "roof_floor_total": round(roof_floor_total, 2),

            "window_north_loss": round(window_north_loss, 2),
            "window_south_loss": round(window_south_loss, 2),
            "window_east_loss": round(window_east_loss, 2),
            "window_west_loss": round(window_west_loss, 2),
            "window_total": round(window_total, 2),

            "door_north_loss": round(door_north_loss, 2),
            "door_south_loss": round(door_south_loss, 2),
            "door_east_loss": round(door_east_loss, 2),
            "door_west_loss": round(door_west_loss, 2),
            "door_total": round(door_total, 2),

            "envelope_total": round(envelope_total, 2),
            "annual_heat_demand_kwh": round(annual_heat_demand_kwh, 2),
            "solar_gain_kwh": round(solar_gain_kwh, 2),
            "adjusted_heat_demand_kwh": round(adjusted_heat_demand_kwh, 2),
            "specific_heat_demand": round(specific_heat_demand, 2),

            "rating_label": rating["label"],
            "rating_color": rating["color"],
            "rating_message": rating["message"]
        })

    except Exception as e:
        return JsonResponse({
            "ok": False,
            "errors": [f"Unerwarteter Fehler: {str(e)}"]
        }, status=500)


@csrf_exempt
def calculate_system(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)

        heat_demand_net = safe_float(data.get("heat_demand_net"))
        bgf = safe_float(data.get("bgf"))

        heating_system = data.get("heating_system", "gas")
        efficiency = safe_float(data.get("efficiency"), DEFAULT_EFFICIENCY)
        cop = safe_float(data.get("cop"), DEFAULT_COP)

        hotwater_demand = safe_float(data.get("hotwater_demand"), DEFAULT_HOTWATER_DEMAND)
        auxiliary_electricity = safe_float(data.get("auxiliary_electricity"), DEFAULT_AUXILIARY_ELECTRICITY)

        errors = []

        validate_non_negative("Heizwärmebedarf netto", heat_demand_net, errors)
        validate_non_negative("BGF", bgf, errors)
        validate_non_negative("Warmwasserbedarf", hotwater_demand, errors)
        validate_non_negative("Hilfsstrom", auxiliary_electricity, errors)

        if bgf == 0:
            errors.append("BGF darf nicht 0 sein.")

        if heating_system not in VALID_HEATING_SYSTEMS:
            errors.append("Ungültiges Heizsystem.")

        if efficiency <= MIN_EFFICIENCY or efficiency > MAX_EFFICIENCY:
            errors.append(f"Wirkungsgrad muss > {MIN_EFFICIENCY} und plausibel sein (z. B. 0.85 bis 1.0).")

        if cop <= MIN_COP or cop > MAX_COP:
            errors.append(f"COP muss > {MIN_COP} und plausibel sein (z. B. 2.5 bis 5.0).")

        if errors:
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        if heating_system == "heatpump":
            heating_end_energy = heat_demand_net / cop
            hotwater_end_energy = hotwater_demand / cop
        else:
            heating_end_energy = heat_demand_net / efficiency
            hotwater_end_energy = hotwater_demand / efficiency

        total_end_energy = heating_end_energy + hotwater_end_energy + auxiliary_electricity

        primary_energy = total_end_energy * PRIMARY_ENERGY_FACTORS[heating_system]
        co2_emissions = total_end_energy * CO2_FACTORS[heating_system]

        specific_end_energy = total_end_energy / bgf
        specific_primary_energy = primary_energy / bgf

        if specific_primary_energy <= SYSTEM_RATING_THRESHOLDS['efficient']:
            system_label = "Sehr effizient"
            system_color = "green"
            system_message = "Die Anlagentechnik arbeitet energetisch günstig."
        elif specific_primary_energy <= SYSTEM_RATING_THRESHOLDS['medium']:
            system_label = "Mittel"
            system_color = "yellow"
            system_message = "Die Anlagentechnik ist nutzbar, aber optimierbar."
        else:
            system_label = "Verbesserungsbedarf"
            system_color = "red"
            system_message = "Die Anlagentechnik verursacht hohe Primärenergieverbräuche."

        return JsonResponse({
            "ok": True,
            "heating_end_energy": round(heating_end_energy, 2),
            "hotwater_end_energy": round(hotwater_end_energy, 2),
            "auxiliary_electricity": round(auxiliary_electricity, 2),
            "total_end_energy": round(total_end_energy, 2),
            "primary_energy": round(primary_energy, 2),
            "co2_emissions": round(co2_emissions, 2),
            "specific_end_energy": round(specific_end_energy, 2),
            "specific_primary_energy": round(specific_primary_energy, 2),
            "system_label": system_label,
            "system_color": system_color,
            "system_message": system_message
        })

    except Exception as e:
        return JsonResponse({
            "ok": False,
            "errors": [f"Unerwarteter Fehler: {str(e)}"]
        }, status=500)


# --- NEU: Photovoltaik ---
@csrf_exempt
def calculate_pv(request):
    """
    Photovoltaik (MVP)
    Input: kwp, specific_yield, self_consumption_rate, electricity_price, feed_in_tariff
    Output: annual_yield_kwh, self_consumption_kwh, feed_in_kwh, savings_eur, feed_in_revenue_eur, total_benefit_eur
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)

        kwp = safe_float(data.get("kwp"), 8.0)
        specific_yield = safe_float(data.get("specific_yield"), 950.0)  # kWh/kWp*a
        self_consumption_rate = safe_float(data.get("self_consumption_rate"), 0.30)  # 0..1
        electricity_price = safe_float(data.get("electricity_price"), 0.35)  # €/kWh
        feed_in_tariff = safe_float(data.get("feed_in_tariff"), 0.08)  # €/kWh

        errors = []
        validate_non_negative("PV kWp", kwp, errors)
        validate_non_negative("Spezifischer Ertrag", specific_yield, errors)
        validate_non_negative("Strompreis", electricity_price, errors)
        validate_non_negative("Einspeisevergütung", feed_in_tariff, errors)

        if self_consumption_rate < MIN_G_VALUE or self_consumption_rate > MAX_G_VALUE:
            errors.append(f"Eigenverbrauchsquote muss zwischen {MIN_G_VALUE} und {MAX_G_VALUE} liegen.")

        if kwp == 0:
            errors.append("PV kWp darf nicht 0 sein.")

        if errors:
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        annual_yield_kwh = kwp * specific_yield
        self_consumption_kwh = annual_yield_kwh * self_consumption_rate
        feed_in_kwh = max(0.0, annual_yield_kwh - self_consumption_kwh)

        savings_eur = self_consumption_kwh * electricity_price
        feed_in_revenue_eur = feed_in_kwh * feed_in_tariff
        total_benefit_eur = savings_eur + feed_in_revenue_eur

        return JsonResponse({
            "ok": True,
            "annual_yield_kwh": round(annual_yield_kwh, 2),
            "self_consumption_kwh": round(self_consumption_kwh, 2),
            "feed_in_kwh": round(feed_in_kwh, 2),
            "savings_eur": round(savings_eur, 2),
            "feed_in_revenue_eur": round(feed_in_revenue_eur, 2),
            "total_benefit_eur": round(total_benefit_eur, 2),
        })

    except Exception as e:
        return JsonResponse({"ok": False, "errors": [f"Unerwarteter Fehler: {str(e)}"]}, status=500)


# --- NEU: Energiebilanz (mit PV-Abzug beim Strombezug) ---
@csrf_exempt
def calculate_balance(request):
    """
    Energiebilanz (MVP)
    Input: heat_demand_net_kwh, hotwater_kwh, auxiliary_electricity_kwh, household_electricity_kwh, 
           pv_self_consumption_kwh, electricity_co2_factor
    Output: total_heat_kwh, total_electricity_gross_kwh, grid_electricity_net_kwh, co2_electricity_kg
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)

        heat_demand_net_kwh = safe_float(data.get("heat_demand_net_kwh"), 0.0)
        hotwater_kwh = safe_float(data.get("hotwater_kwh"), 3000.0)
        auxiliary_electricity_kwh = safe_float(data.get("auxiliary_electricity_kwh"), 1200.0)
        household_electricity_kwh = safe_float(data.get("household_electricity_kwh"), 2000.0)
        pv_self_consumption_kwh = safe_float(data.get("pv_self_consumption_kwh"), 0.0)

        electricity_co2_factor = safe_float(data.get("electricity_co2_factor"), 0.40)  # kg/kWh (MVP)

        errors = []
        validate_non_negative("Heizwärmebedarf netto", heat_demand_net_kwh, errors)
        validate_non_negative("Warmwasser", hotwater_kwh, errors)
        validate_non_negative("Hilfsstrom", auxiliary_electricity_kwh, errors)
        validate_non_negative("Haushaltsstrom", household_electricity_kwh, errors)
        validate_non_negative("PV Eigenverbrauch", pv_self_consumption_kwh, errors)
        validate_non_negative("Strom CO2 Faktor", electricity_co2_factor, errors)

        if errors:
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        total_heat_kwh = heat_demand_net_kwh + hotwater_kwh
        total_electricity_gross_kwh = auxiliary_electricity_kwh + household_electricity_kwh
        grid_electricity_net_kwh = max(0.0, total_electricity_gross_kwh - pv_self_consumption_kwh)

        co2_electricity_kg = grid_electricity_net_kwh * electricity_co2_factor

        return JsonResponse({
            "ok": True,
            "total_heat_kwh": round(total_heat_kwh, 2),
            "total_electricity_gross_kwh": round(total_electricity_gross_kwh, 2),
            "grid_electricity_net_kwh": round(grid_electricity_net_kwh, 2),
            "co2_electricity_kg": round(co2_electricity_kg, 2),
        })

    except Exception as e:
        return JsonResponse({"ok": False, "errors": [f"Unerwarteter Fehler: {str(e)}"]}, status=500)


# ===== BAUTECHNIK API (REST Framework) =====
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import (
    Material, MaterialSchicht, Konstruktion, KonstruktionSchicht,
    FensterTyp, TürTyp, SonnenschutzTyp, Gebäude, Bauteil, EkobaudatMaterial
)
from .serializers import (
    MaterialSerializer, MaterialSchichtSerializer, KonstruktionSerializer, KonstruktionSchichtSerializer,
    FensterTypSerializer, TürTypSerializer, SonnenschutzTypSerializer,
    GebäudeSerializer, BauteilSerializer, EkobaudatMaterialSerializer
)


class MaterialViewSet(viewsets.ModelViewSet):
    """CRUD für Baumaterialien"""
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    filterset_fields = ['rohdichte', 'lambda_value']
    search_fields = ['name']


class MaterialSchichtViewSet(viewsets.ModelViewSet):
    """CRUD für Material-Schichten"""
    queryset = MaterialSchicht.objects.all()
    serializer_class = MaterialSchichtSerializer


class KonstruktionViewSet(viewsets.ModelViewSet):
    """CRUD für Konstruktionen (mit U-Wert-Berechnung)"""
    queryset = Konstruktion.objects.all()
    serializer_class = KonstruktionSerializer
    filterset_fields = ['typ']
    search_fields = ['name']


class KonstruktionSchichtViewSet(viewsets.ModelViewSet):
    """CRUD für Konstruktion-Schichten-Zuordnung"""
    queryset = KonstruktionSchicht.objects.all()
    serializer_class = KonstruktionSchichtSerializer


class FensterTypViewSet(viewsets.ModelViewSet):
    """CRUD für Fenstertypen"""
    queryset = FensterTyp.objects.all()
    serializer_class = FensterTypSerializer
    search_fields = ['name']


class TürTypViewSet(viewsets.ModelViewSet):
    """CRUD für Türtypen"""
    queryset = TürTyp.objects.all()
    serializer_class = TürTypSerializer
    search_fields = ['name']


class SonnenschutzTypViewSet(viewsets.ModelViewSet):
    """CRUD für Sonnenschutztypen"""
    queryset = SonnenschutzTyp.objects.all()
    serializer_class = SonnenschutzTypSerializer
    filterset_fields = ['position', 'typ']
    search_fields = ['name']


class GebäudeViewSet(viewsets.ModelViewSet):
    """CRUD für Gebäude"""
    queryset = Gebäude.objects.all()
    serializer_class = GebäudeSerializer
    search_fields = ['name', 'standort']

    @action(detail=True, methods=['get'])
    def kennwerte(self, request, pk=None):
        """Berechne Kennwerte für Gebäude"""
        gebäude = self.get_object()
        bauteile = gebäude.bauteile.all()

        total_h = sum(b.transmissionsverlust for b in bauteile)
        annual_heat_demand = (total_h * gebäude.gradstunden) / 1000
        specific_heat_demand = annual_heat_demand / gebäude.bgf if gebäude.bgf > 0 else 0

        return Response({
            'gebäude_id': gebäude.id,
            'total_h': round(total_h, 2),
            'annual_heat_demand_kwh': round(annual_heat_demand, 2),
            'specific_heat_demand': round(specific_heat_demand, 2),
        })


class BauteilViewSet(viewsets.ModelViewSet):
    """CRUD für Bauteile (Flächen)"""
    queryset = Bauteil.objects.all()
    serializer_class = BauteilSerializer
    filterset_fields = ['gebäude', 'orientierung']
    search_fields = ['name', 'gebäude__name']


class EkobaudatMaterialViewSet(viewsets.ModelViewSet):
    """CRUD für ÖKOBAUDAT Materialien (Hülle, Wände, etc.)"""
    queryset = EkobaudatMaterial.objects.all()
    serializer_class = EkobaudatMaterialSerializer
    filterset_fields = ['category']
    search_fields = ['name', 'producer', 'category']

    THERMAL_PRESETS = {
        8: {'lambda_value': 0.80, 'default_thickness_mm': 365},
        354: {'lambda_value': 0.45, 'default_thickness_mm': 300},
        1332: {'lambda_value': 0.35, 'default_thickness_mm': 240},
        1312: {'lambda_value': 1.40, 'default_thickness_mm': 18},
        1108: {'lambda_value': 0.17, 'default_thickness_mm': 10},
        352: {'lambda_value': 1.90, 'default_thickness_mm': 60},
        661: {'lambda_value': 2.10, 'default_thickness_mm': 200},
    }

    WINDOW_PRESETS = {
        603: {'u_value': 1.30, 'g_value': 0.63},
        604: {'u_value': 0.80, 'g_value': 0.55},
        609: {'u_value': 1.20, 'g_value': 0.63},
        610: {'u_value': 0.90, 'g_value': 0.55},
        1049: {'u_value': 0.80, 'g_value': 0.55},
    }

    DOOR_PRESETS = {
        2001: {'u_value': 2.5},   # Holztür (Altbau)
        2002: {'u_value': 1.3},   # Kunststoff-Haustür PVC (KfW-55)
        2003: {'u_value': 0.95},  # Holz-Alu-Kompo (KfW-40)
        2004: {'u_value': 2.2},   # Aluminium-Fassadentür
        2005: {'u_value': 3.5},   # Stahlzarge Innentür
        2006: {'u_value': 1.8},   # Kunststoff-Nebeneingangstür
        2007: {'u_value': 0.55},  # Industrie-Sectionaltore
    }
    
    def get_queryset(self):
        """Filter nach Kategorie wenn parameter 'category' gegeben"""
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset
    
    @action(detail=False, methods=['get'])
    def popular_walls(self, request):
        """Beliebte Wandmaterialien mit einfachen Namen für UI"""
        materials = [
            {'id': 8, 'simple_name': 'Ziegelwand', 'category': 'wall'},
            {'id': 354, 'simple_name': 'Leichtbeton-Block', 'category': 'wall'},
            {'id': 1332, 'simple_name': 'Leichtbeton-Stein', 'category': 'wall'},
        ]
        return Response(materials)
    
    @action(detail=False, methods=['get'])
    def popular_insulation(self, request):
        """Beliebte Dämmstoffe mit einfachen Namen"""
        materials = [
            {'id': 1207, 'simple_name': 'XPS-Dämmung', 'category': 'insulation'},
            {'id': 1240, 'simple_name': 'Mineralwolle-Dämmung', 'category': 'insulation'},
        ]
        return Response(materials)
    
    @action(detail=False, methods=['get'])
    def popular_plaster(self, request):
        """Beliebte Putze mit einfachen Namen"""
        materials = [
            {'id': 1277, 'simple_name': 'Kalkputz', 'category': 'plaster'},
            {'id': 1279, 'simple_name': 'Kalk-Zementputz', 'category': 'plaster'},
            {'id': 1281, 'simple_name': 'Gipsputz', 'category': 'plaster'},
            {'id': 1282, 'simple_name': 'Lehmputz', 'category': 'plaster'},
            {'id': 1214, 'simple_name': 'Silikat-(Dispersions)putz', 'category': 'plaster'},
            {'id': 1273, 'simple_name': 'Kunstharzputz', 'category': 'plaster'},
            {'id': 1216, 'simple_name': 'Kratzputz (mineralisch)', 'category': 'plaster'},
        ]
        return Response(materials)

    @action(detail=False, methods=['get'])
    def popular_doors(self, request):
        """Beliebte Türtypen / Eingänge für UI"""
        doors = [
            {'id': 2001, 'simple_name': 'Holztür (Altbau-Standard)', 'category': 'door', **self.DOOR_PRESETS[2001]},
            {'id': 2002, 'simple_name': 'Kunststoff-Haustür (KfW-55)', 'category': 'door', **self.DOOR_PRESETS[2002]},
            {'id': 2003, 'simple_name': 'Holz-Alu-Komposition (KfW-40)', 'category': 'door', **self.DOOR_PRESETS[2003]},
            {'id': 2004, 'simple_name': 'Aluminium-Fassadentür', 'category': 'door', **self.DOOR_PRESETS[2004]},
            {'id': 2005, 'simple_name': 'Stahlzarge Innentür', 'category': 'door', **self.DOOR_PRESETS[2005]},
            {'id': 2006, 'simple_name': 'Kunststoff-Nebeneingangstür', 'category': 'door', **self.DOOR_PRESETS[2006]},
            {'id': 2007, 'simple_name': 'Industrie-Sectionaltore', 'category': 'door', **self.DOOR_PRESETS[2007]},
        ]
        return Response(doors)

    @action(detail=True, methods=['get'])
    def thermal_u(self, request, pk=None):
        """Berechnet einen U-Wert aus hinterlegter Lambda-Annahme und Dicke."""
        material = self.get_object()

        window_preset = self.WINDOW_PRESETS.get(material.id)
        if window_preset:
            return Response({
                'id': material.id,
                'name': material.name,
                'u_value': window_preset['u_value'],
                'g_value': window_preset['g_value'],
                'lambda_value': None,
                'thickness_mm': None,
                'default_thickness_mm': None,
                'formula': 'window_preset',
            })

        door_preset = self.DOOR_PRESETS.get(material.id)
        if door_preset:
            return Response({
                'id': material.id,
                'name': material.name,
                'u_value': door_preset['u_value'],
                'lambda_value': None,
                'thickness_mm': None,
                'default_thickness_mm': None,
                'formula': 'door_preset',
            })

        if material.u_value is not None:
            return Response({
                'id': material.id,
                'name': material.name,
                'u_value': material.u_value,
                'lambda_value': None,
                'thickness_mm': None,
                'default_thickness_mm': None,
                'formula': 'stored_u_value',
            })

        thermal_preset = self.THERMAL_PRESETS.get(material.id)
        if not thermal_preset:
            return Response({
                'id': material.id,
                'name': material.name,
                'u_value': None,
                'lambda_value': None,
                'thickness_mm': None,
                'default_thickness_mm': None,
                'formula': 'not_available',
            }, status=200)

        lambda_value = thermal_preset['lambda_value']
        thickness_mm = safe_float(request.query_params.get('thickness_mm'), thermal_preset['default_thickness_mm'])
        if thickness_mm <= 0:
            thickness_mm = thermal_preset['default_thickness_mm']

        thickness_m = thickness_mm / 1000.0
        r_si = 0.13
        r_se = 0.04
        u_value = 1 / (r_si + (thickness_m / lambda_value) + r_se)

        return Response({
            'id': material.id,
            'name': material.name,
            'u_value': round(u_value, 3),
            'lambda_value': lambda_value,
            'thickness_mm': thickness_mm,
            'default_thickness_mm': thermal_preset['default_thickness_mm'],
            'formula': '1 / (Rsi + d/lambda + Rse)',
        })
    
    @action(detail=False, methods=['get'])
    def popular_roof(self, request):
        """Beliebte Dach-Materialien mit einfachen Namen"""
        materials = [
            {'id': 1312, 'simple_name': 'Dachsteine', 'category': 'roof'},
            {'id': 1108, 'simple_name': 'Bitumendachbahn', 'category': 'roof'},
        ]
        return Response(materials)
    
    @action(detail=False, methods=['get'])
    def popular_floor(self, request):
        """Beliebte Boden-Materialien mit einfachen Namen"""
        materials = [
            {'id': 352, 'simple_name': 'Estrich', 'category': 'floor'},
            {'id': 661, 'simple_name': 'Betonplatte', 'category': 'floor'},
        ]
        return Response(materials)

    @action(detail=False, methods=['get'])
    def popular_windows(self, request):
        """Beliebte Fenstertypen / Verglasungen aus ÖKOBAUDAT für UI"""
        materials = [
            {'id': 603, 'simple_name': 'Fenster - 2-fach Verglasung (Holz)', 'category': 'window', **self.WINDOW_PRESETS[603]},
            {'id': 604, 'simple_name': 'Fenster - 3-fach Verglasung (Holz)', 'category': 'window', **self.WINDOW_PRESETS[604]},
            {'id': 609, 'simple_name': 'Kunststofffenster - 2-fach Verglasung', 'category': 'window', **self.WINDOW_PRESETS[609]},
            {'id': 610, 'simple_name': 'Kunststofffenster - 3-fach Verglasung', 'category': 'window', **self.WINDOW_PRESETS[610]},
            {'id': 1049, 'simple_name': 'Dreifachverglasung (generisch)', 'category': 'window', **self.WINDOW_PRESETS[1049]},
        ]
        return Response(materials)