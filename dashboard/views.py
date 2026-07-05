import json
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt

# Importiere zentrale Hilfsfunktionen. Die GEG-/DIN-Faktoren (Primärenergie, CO₂) liegen
# bewusst in den Service-Modulen (din18599_anlage.py: F_PRIMARY/F_CO2), nicht in constants.py –
# die dortigen Faktor-Tabellen sind eine ältere, hier nicht genutzte Vereinfachung.
from .utils import safe_float, validate_non_negative, validate_u_value, get_rating
from .services.din18599 import calculate_heat_demand
from .services.din18599_anlage import calculate_system_din
from .services.din4108 import (
    pruefe_mindestwaermeschutz,
    berechne_sommerlicher_waermeschutz,
    berechne_tauwasser_glaser,
    pruefe_luftdichtheit,
    material_db,
)


def home(request):
    """Dashboard-Startseite: gespeicherte Projekte ansehen + neues Projekt anlegen."""
    return render(request, "dashboard/dashboard_home.html")


def index(request):
    return render(request, "dashboard/index.html")


@csrf_exempt
def calculate(request):
    """Heizwärmebedarf nach DIN V 18599-2 (Monatsbilanzverfahren).

    Die eigentliche Rechenlogik liegt in dashboard/services/din18599.py.
    Siehe docs/DIN18599_Umsetzung.md für die normative Herleitung.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)
        result = calculate_heat_demand(data)
        status = 200 if result.get("ok") else 400
        return JsonResponse(result, status=status)
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "errors": [f"Unerwarteter Fehler: {str(e)}"]
        }, status=500)


@csrf_exempt
def calculate_system(request):
    """Anlagentechnik nach DIN V 18599-5/-6/-8 (Stufe 2).

    Nutzenergie → Übergabe → Verteilung → Speicherung → Erzeugung → End-/Primärenergie.
    Rechenlogik in dashboard/services/din18599_anlage.py; normative Herleitung in
    docs/DIN18599_Umsetzung.md (Abschnitte 7–9).
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)
        result = calculate_system_din(data)
        status = 200 if result.get("ok") else 400
        return JsonResponse(result, status=status)
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "errors": [f"Unerwarteter Fehler: {str(e)}"]
        }, status=500)


# ===========================================================================
# DIN 4108 – Bauphysikalische Nachweise (Rechenlogik: services/din4108.py;
# normative Herleitung: docs/DIN4108_Umsetzung.md)
# ===========================================================================
@csrf_exempt
def calculate_mindestwaermeschutz(request):
    """Mindestwärmeschutz-Nachweis je Bauteil (DIN 4108-2:2026-05, §5, Tab. 3)."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)
    try:
        data = json.loads(request.body)
        result = pruefe_mindestwaermeschutz(data)
        return JsonResponse(result, status=200 if result.get("ok") else 400)
    except Exception as e:
        return JsonResponse({"ok": False, "errors": [f"Unerwarteter Fehler: {str(e)}"]}, status=500)


@csrf_exempt
def calculate_sommerlicher_waermeschutz(request):
    """Sommerlicher Wärmeschutz – Sonneneintragskennwert (DIN 4108-2:2026-05, §8.4)."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)
    try:
        data = json.loads(request.body)
        result = berechne_sommerlicher_waermeschutz(data)
        return JsonResponse(result, status=200 if result.get("ok") else 400)
    except Exception as e:
        return JsonResponse({"ok": False, "errors": [f"Unerwarteter Fehler: {str(e)}"]}, status=500)


@csrf_exempt
def calculate_tauwasser(request):
    """Tauwassernachweis / Glaser-Periodenbilanzverfahren (DIN 4108-3:2024-03)."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)
    try:
        data = json.loads(request.body)
        result = berechne_tauwasser_glaser(data)
        return JsonResponse(result, status=200 if result.get("ok") else 400)
    except Exception as e:
        return JsonResponse({"ok": False, "errors": [f"Unerwarteter Fehler: {str(e)}"]}, status=500)


@csrf_exempt
def calculate_luftdichtheit(request):
    """Luftdichtheit n50-Nachweis (DIN 4108-7:2026-04, §5)."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)
    try:
        data = json.loads(request.body)
        result = pruefe_luftdichtheit(data)
        return JsonResponse(result, status=200 if result.get("ok") else 400)
    except Exception as e:
        return JsonResponse({"ok": False, "errors": [f"Unerwarteter Fehler: {str(e)}"]}, status=500)


def din4108_materialien(request):
    """Material-Bemessungswerte (λ/μ, DIN 4108-4) für den Glaser-Schichteditor."""
    return JsonResponse({"ok": True, "materialien": material_db()}, status=200)


# --- Photovoltaik nach DIN V 18599-9 (Gl. 64–67, Anhang B) ---
# Q_el,prod,PV = E_sol · (P_pk/I_ref) · f_perf  je Monat;  P_pk = k_pk · A (Gl. 67)
# k_pk (Tab. B.2, ab 2017): mono 0,182 / poly 0,166 kW/m²
# f_perf (Tab. B.1, kristallin): integriert/unbelüftet 0,70 · mäßig belüftet 0,75 ·
#                                stark belüftet/freistehend 0,80
PV_K_PK = {"mono": 0.182, "poly": 0.166}
PV_F_PERF = {"integrated": 0.70, "ventilated": 0.75, "free": 0.80}

# Monatliche Strahlung auf PV-Flächen (Teil 10 Tab. E.6, 24-h-Mittel W/m²).
# Fassaden = exakte 90°-Werte. Geneigte Dachflächen werden aus realer Neigung und
# Ausrichtung interpoliert (siehe _tilted_irradiation).
from .services.din18599 import I_S as _I_S, MONTH_DAYS as _MDAYS
from .services.climate import resolve_region as _resolve_region
import math as _math

# --- Strahlung auf beliebig geneigte/ausgerichtete Flächen (DIN-verankert) ---
# Reihenfolge der 8 vertikalen Referenzorientierungen im Uhrzeigersinn ab Nord.
_VERT_ORDER = ["north", "northeast", "east", "southeast",
               "south", "southwest", "west", "northwest"]


def _vertical_irradiation(month, azimuth_from_south):
    """Monatl. Strahlung auf eine VERTIKALE Fläche (90°) für beliebigen Azimut,
    linear interpoliert zwischen den 8 DIN-Referenzorientierungen (Teil 10 Tab. E.6).
    azimuth_from_south: 0=Süd, negativ=Ost, positiv=West [Grad]."""
    comp = (180.0 + azimuth_from_south) % 360.0      # Kompass: 0=N … 180=S
    idx = comp / 45.0
    lo = int(_math.floor(idx)) % 8
    hi = (lo + 1) % 8
    frac = idx - _math.floor(idx)
    return (_I_S[_VERT_ORDER[lo]][month] * (1.0 - frac)
            + _I_S[_VERT_ORDER[hi]][month] * frac)


def _tilt_weights(tilt_deg):
    """Gewichte a (Horizontal-Anteil) und b (Vertikal-Anteil) der Strahlung auf eine
    geneigte Fläche – stückweise linear durch die Stützstellen (0°: 1/0),
    (40°: 0,72/0,48) und (90°: 0/1). Der 40°-Punkt ist der DIN-kalibrierte
    Dach-Süd-Wert (Jahressumme ≈ Süd-45°-Zeile der Norm)."""
    t = max(0.0, min(90.0, tilt_deg))
    if t <= 40.0:
        f = t / 40.0
        return (1.0 + (0.72 - 1.0) * f, 0.48 * f)
    f = (t - 40.0) / 50.0
    return (0.72 * (1.0 - f), 0.48 + (1.0 - 0.48) * f)


def _tilted_irradiation(month, tilt_deg, azimuth_from_south):
    """Monatl. Strahlung [W/m²] auf eine Fläche mit Neigung tilt_deg (0=flach,
    90=senkrecht) und Ausrichtung azimuth_from_south (0=Süd)."""
    a, b = _tilt_weights(tilt_deg)
    return (a * _I_S["horizontal"][month]
            + b * _vertical_irradiation(month, azimuth_from_south))


@csrf_exempt
def calculate_pv(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)

        area_roof = safe_float(data.get("area_roof_m2"), 0.0)
        area_south = safe_float(data.get("area_south_m2"), 0.0)
        area_ew = safe_float(data.get("area_ew_m2"), 0.0)
        cell = str(data.get("cell_type", "mono")).strip().lower()
        mounting = str(data.get("mounting", "ventilated")).strip().lower()
        shading = min(max(safe_float(data.get("shading"), 0.05), 0.0), 0.5)
        # Dach-Geometrie: Neigung 0–90° (Default 35° ≈ optimal DE) und Ausrichtung als
        # Abweichung von Süd (−180…180°, negativ=Ost, positiv=West).
        roof_tilt = min(max(safe_float(data.get("roof_tilt_deg"), 35.0), 0.0), 90.0)
        roof_azimuth = min(max(safe_float(data.get("roof_azimuth_deg"), 0.0), -180.0), 180.0)
        self_rate = safe_float(data.get("self_consumption_rate"), 0.30)
        electricity_price = safe_float(data.get("electricity_price"), 0.35)
        feed_in_tariff = safe_float(data.get("feed_in_tariff"), 0.08)

        errors = []
        total_area = area_roof + area_south + area_ew
        if total_area <= 0:
            errors.append("Gesamte PV-Fläche muss > 0 m² sein.")
        if not (0.0 <= self_rate <= 1.0):
            errors.append("Eigenverbrauchsquote muss zwischen 0 und 1 liegen.")
        if errors:
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        k_pk = PV_K_PK.get(cell, PV_K_PK["mono"])
        f_perf = PV_F_PERF.get(mounting, PV_F_PERF["ventilated"])

        # Klimaregion aus dem Standort (Bundesland): regionaler Strahlungsfaktor
        # skaliert die Potsdam-Referenzstrahlung auf das lokale Niveau → wirkt
        # direkt auf Monats- und Jahresertrag.
        region = _resolve_region(data.get("project_state"))
        radiation_factor = float(region["radiation_factor"])

        monthly = []
        annual = 0.0
        # Jahresertrag je Orientierung getrennt mitführen (für Aufschlüsselung/Tabelle)
        ann_roof = ann_south = ann_ew = 0.0
        for m in range(12):
            hours = _MDAYS[m] * 24.0
            # E_sol je Fläche [kWh/m² im Monat] (Gl. 66), regional skaliert.
            # Dach: reale Neigung + Ausrichtung; Fassaden: vertikal (90°).
            e_roof = _tilted_irradiation(m, roof_tilt, roof_azimuth) * radiation_factor * hours / 1000.0
            e_south = _I_S["south"][m] * radiation_factor * hours / 1000.0
            e_ew = 0.5 * (_I_S["east"][m] + _I_S["west"][m]) * radiation_factor * hours / 1000.0
            # Gl. (64): E_sol · P_pk/I_ref · f_perf  – P_pk/A = k_pk, I_ref = 1 kW/m²
            f_sys = k_pk * f_perf * (1.0 - shading)
            q_roof = e_roof * area_roof * f_sys
            q_south = e_south * area_south * f_sys
            q_ew = e_ew * area_ew * f_sys
            q_m = q_roof + q_south + q_ew
            monthly.append(round(q_m, 1))
            annual += q_m
            ann_roof += q_roof
            ann_south += q_south
            ann_ew += q_ew

        p_pk_total = k_pk * total_area
        self_consumption_kwh = annual * self_rate
        feed_in_kwh = max(0.0, annual - self_consumption_kwh)
        savings_eur = self_consumption_kwh * electricity_price
        feed_in_revenue_eur = feed_in_kwh * feed_in_tariff

        def _orient(key, label, area, ann):
            return {
                "key": key,
                "label": label,
                "area_m2": round(area, 1),
                "kwp": round(k_pk * area, 2),
                "annual_kwh": round(ann, 1),
                "specific_kwh_kwp": round(ann / (k_pk * area), 0) if area > 0 else 0,
                "share_pct": round(ann / annual * 100, 1) if annual > 0 else 0,
            }

        by_orientation = [
            _orient("roof", "Dach (Süd ~40°)", area_roof, ann_roof),
            _orient("south", "Süd-Fassade (90°)", area_south, ann_south),
            _orient("ew", "Ost/West-Fassade (90°)", area_ew, ann_ew),
        ]

        return JsonResponse({
            "ok": True,
            "installed_kwp": round(p_pk_total, 2),
            "annual_yield_kwh": round(annual, 1),
            "specific_yield_kwh_kwp": round(annual / p_pk_total, 0) if p_pk_total > 0 else 0,
            "self_consumption_kwh": round(self_consumption_kwh, 1),
            "feed_in_kwh": round(feed_in_kwh, 1),
            "savings_eur": round(savings_eur, 2),
            "feed_in_revenue_eur": round(feed_in_revenue_eur, 2),
            "total_benefit_eur": round(savings_eur + feed_in_revenue_eur, 2),
            "co2_savings_kg": round(annual * 0.56, 1),
            "monthly_yield_kwh": monthly,
            "by_orientation": by_orientation,
            "k_pk": k_pk,
            "f_perf": f_perf,
            "climate_region_label": region["label"],
            "climate_radiation_factor": round(radiation_factor, 2),
            "roof_tilt_deg": round(roof_tilt, 0),
            "roof_azimuth_deg": round(roof_azimuth, 0),
            "calculation_basis": "DIN V 18599-9:2018-09, Gl. 64–67 + Anhang B",
        })

    except Exception as e:
        return JsonResponse({"ok": False, "errors": [f"Unerwarteter Fehler: {str(e)}"]}, status=500)


# --- Energiebilanz: Endenergie-konsistente Gesamtbilanz inkl. PV-Verrechnung ---
@csrf_exempt
def calculate_balance(request):
    """
    Gesamtbilanz auf ENDenergie-Ebene (konsistent zur DIN-Anlagentechnik):
      - fuel_end_kwh:        Brennstoff-Endenergie (Gas/Pellet/Fernwärme) aus /calculate-system/
      - system_electricity_kwh: Strom der Anlagentechnik (Hilfsstrom + ggf. WP-Heiz-/WW-Strom)
      - household_electricity_kwh: Haushaltsstrom (Nutzereingabe)
      - pv_self_consumption_kwh:   PV-Eigenverbrauch (verrechnet nur gegen Strom)
      - system_co2_kg:       CO₂ der Anlagentechnik (bereits Brennstoff + Anlagenstrom)
    CO₂ gesamt = system_co2 + Haushaltsstrom·f − PV-Eigenverbrauch·f  (f = 0,56 kg/kWh Netzstrom, GEG)
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)

        fuel_end_kwh = safe_float(data.get("fuel_end_kwh"), 0.0)
        system_electricity_kwh = safe_float(data.get("system_electricity_kwh"), 0.0)
        household_electricity_kwh = safe_float(data.get("household_electricity_kwh"), 2000.0)
        pv_self_consumption_kwh = safe_float(data.get("pv_self_consumption_kwh"), 0.0)
        system_co2_kg = safe_float(data.get("system_co2_kg"), 0.0)
        co2_factor_el = safe_float(data.get("electricity_co2_factor"), 0.56)  # GEG Anlage 9

        errors = []
        validate_non_negative("Brennstoff-Endenergie", fuel_end_kwh, errors)
        validate_non_negative("Anlagenstrom", system_electricity_kwh, errors)
        validate_non_negative("Haushaltsstrom", household_electricity_kwh, errors)
        validate_non_negative("PV Eigenverbrauch", pv_self_consumption_kwh, errors)
        if errors:
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        electricity_gross_kwh = system_electricity_kwh + household_electricity_kwh
        # PV-Eigenverbrauch kann nur tatsächlich verbrauchten Strom ersetzen
        pv_offset_kwh = min(pv_self_consumption_kwh, electricity_gross_kwh)
        grid_electricity_net_kwh = electricity_gross_kwh - pv_offset_kwh

        total_end_energy_kwh = fuel_end_kwh + electricity_gross_kwh
        co2_total_kg = max(system_co2_kg + household_electricity_kwh * co2_factor_el
                           - pv_offset_kwh * co2_factor_el, 0.0)

        return JsonResponse({
            "ok": True,
            "total_end_energy_kwh": round(total_end_energy_kwh, 2),
            "fuel_end_kwh": round(fuel_end_kwh, 2),
            "total_electricity_gross_kwh": round(electricity_gross_kwh, 2),
            "grid_electricity_net_kwh": round(grid_electricity_net_kwh, 2),
            "pv_offset_kwh": round(pv_offset_kwh, 2),
            "co2_total_kg": round(co2_total_kg, 2),
            # Abwärtskompatibel (alte Anzeige):
            "co2_electricity_kg": round(grid_electricity_net_kwh * co2_factor_el, 2),
        })

    except Exception as e:
        return JsonResponse({"ok": False, "errors": [f"Unerwarteter Fehler: {str(e)}"]}, status=500)


@csrf_exempt
def upload_ekobaudat_csv(request):
    """Upload von ÖKOBAUDAT-Materialdaten als CSV **oder** Excel (.xlsx/.xls).

    Multipart-POST mit Feld 'csv_file' (oder 'file'). Der offizielle ÖKOBAUDAT-Export
    (Spalten UUID/Modul/Name (de)) wird automatisch erkannt und über den GWP-Importpfad
    (Modul A1–A3) eingelesen; andere Tabellen über den generischen Spalten-Matcher.
    """
    if request.method != 'POST':
        return JsonResponse({"ok": False, "errors": ["Only POST allowed"]}, status=400)

    upload = request.FILES.get('csv_file') or request.FILES.get('file')
    if upload is None:
        return JsonResponse({"ok": False, "errors": ["Keine Datei gefunden."]}, status=400)

    from .csv_utils import read_csv_bytes, read_excel_bytes, import_material_rows
    from .models import EkobaudatMaterial

    name = (upload.name or "").lower()
    raw = upload.read()

    try:
        if name.endswith((".xlsx", ".xlsm", ".xls")):
            rows = read_excel_bytes(raw, name)
        elif name.endswith((".csv", ".txt")):
            rows = read_csv_bytes(raw)
        else:
            return JsonResponse(
                {"ok": False, "errors": ["Nur CSV- (.csv) oder Excel-Dateien (.xlsx/.xls) werden unterstützt."]},
                status=400)
    except ValueError as read_err:
        return JsonResponse({"ok": False, "errors": [str(read_err)]}, status=400)
    except Exception as read_err:
        import traceback
        traceback.print_exc()
        return JsonResponse({"ok": False, "errors": [f"Datei konnte nicht gelesen werden: {read_err}"]}, status=400)

    if not rows:
        return JsonResponse({"ok": False, "errors": ["Die Datei enthält keine Datenzeilen."]}, status=400)

    try:
        result = import_material_rows(rows, EkobaudatMaterial, source_name=upload.name)
    except Exception as import_err:
        import traceback
        traceback.print_exc()
        return JsonResponse({"ok": False, "errors": [f"Import fehlgeschlagen: {import_err}"]}, status=500)

    imported = result.get("imported", 0)
    updated = result.get("updated", 0)
    skipped = result.get("skipped", 0)
    return JsonResponse({
        "ok": True,
        "success": True,
        "file": result.get("file", upload.name),
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "total": result.get("rows", imported + updated + skipped),
        "message": f"{imported} neue Materialien importiert, {updated} aktualisiert",
    })


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

    PRESET_METADATA = {
        8: {'name': 'Ziegelwand', 'category': 'wall'},
        354: {'name': 'Leichtbeton-Block', 'category': 'wall'},
        1332: {'name': 'Kalksandstein', 'category': 'wall'},
        1312: {'name': 'Dachsteine', 'category': 'roof'},
        1108: {'name': 'Bitumendachbahn', 'category': 'roof'},
        352: {'name': 'Estrich', 'category': 'floor'},
        661: {'name': 'Betonplatte', 'category': 'floor'},
        603: {'name': 'Fenster Typ 603', 'category': 'window'},
        604: {'name': 'Fenster Typ 604', 'category': 'window'},
        609: {'name': 'Fenster Typ 609', 'category': 'window'},
        610: {'name': 'Fenster Typ 610', 'category': 'window'},
        1049: {'name': 'Fenster Typ 1049', 'category': 'window'},
        2001: {'name': 'Holztür (Altbau-Standard)', 'category': 'door'},
        2002: {'name': 'Kunststoff-Haustür (KfW-55)', 'category': 'door'},
        2003: {'name': 'Holz-Alu-Komposition (KfW-40)', 'category': 'door'},
        2004: {'name': 'Aluminium-Fassadentür', 'category': 'door'},
        2005: {'name': 'Stahlzarge Innentür', 'category': 'door'},
        2006: {'name': 'Kunststoff-Nebeneingangstür', 'category': 'door'},
        2007: {'name': 'Industrie-Sectionaltore', 'category': 'door'},
        4001: {'name': 'Passivhaus-Bodenplatte (200 mm Dämmung)', 'category': 'floor'},
        4002: {'name': 'Neubau gut gedämmt (120 mm)', 'category': 'floor'},
        4003: {'name': 'GEG-Referenz (100 mm Dämmung)', 'category': 'floor'},
        4004: {'name': 'Altbau leicht gedämmt (50 mm)', 'category': 'floor'},
        4005: {'name': 'Altbau ungedämmt (Betonplatte + Estrich)', 'category': 'floor'},
    }

    # Wärmeleitfähigkeiten λ nach DIN 4108-4 (Bemessungswerte) – NICHT aus der
    # ÖKOBAUDAT (die enthält keine λ-/U-Werte, nur Ökobilanz-Indikatoren).
    THERMAL_PRESETS = {
        8: {'lambda_value': 0.80, 'default_thickness_mm': 365},    # Vollziegel ~1800 kg/m³
        354: {'lambda_value': 0.45, 'default_thickness_mm': 300},  # Leichtbeton ~1000 kg/m³
        1332: {'lambda_value': 0.99, 'default_thickness_mm': 240}, # Kalksandstein 1800 kg/m³ (war fälschlich 0,35)
        1312: {'lambda_value': 1.40, 'default_thickness_mm': 18},  # Dachsteine (Beton)
        1108: {'lambda_value': 0.17, 'default_thickness_mm': 10},  # Bitumenbahn
        352: {'lambda_value': 1.40, 'default_thickness_mm': 60},   # Zementestrich (war 1,90)
        661: {'lambda_value': 2.10, 'default_thickness_mm': 200},  # Beton bewehrt
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

    # Zuordnung Wandschicht-Material (Frontend-Schlüssel) → ÖKOBAUDAT-Datensatz (UUID).
    # Gewählt wurden generische/durchschnittliche Datensätze (Typ average/generic) aus
    # OBD_2024; GWP = Modul A1–A3 (Herstellung, "graue Emissionen").
    LAYER_OBD_MAP = {
        "gipsputz":      "7e0c008a-009d-4357-92c1-afb2cec3bc0a",  # Gipsputz (innen), m³
        "kalkputz":      "ddc96ae4-086c-4033-9e45-c5589f1661ba",  # Kalkputzmörtel, m³
        "kalk_zement_i": "af98c17b-b748-4d08-b5d5-9ff028ae7f25",  # Kalkzementmörtel, m³
        "lehmputz":      "422b2446-8a3f-457d-b47b-4728b2869d86",  # Lehmputz, m³
        "8":             "30514538-fcb4-483b-b5d5-c108d2037536",  # Mauerziegel (ungefüllt), m³
        "354":           "a1deced7-6fa9-4266-bc86-da75b3653b06",  # Leichtbetonstein Naturbims, m³
        "1332":          "cc0d7baa-755a-4a4a-baf3-4fe53d68a041",  # Kalksandstein, 1000 kg
        "stahlbeton":    "8347f9a7-f4ec-4a36-a266-a0281f5fd16d",  # Beton C25/30, m³ (ohne Bewehrung)
        "holz_mass":     "55a6caa5-0c2f-410f-b752-f78e20ed93fa",  # Konstruktionsvollholz, m³
        "kleber_wdvs":   "96171066-34d9-4b33-b1e6-3af1ea11db61",  # Zementmörtel, m³
        "eps":           "757297f1-9325-4df4-af51-96510be76bf3",  # EPS-Hartschaum 20 kg/m³, m³
        "xps":           "b452a1d8-b252-4f3b-914d-1b19bd268a2e",  # XPS, m³
        "mw":            "699e3d57-72b4-402d-a0ee-cebb06f3cdf1",  # Mineralwolle (mittlere Rohdichte), m³
        "pur":           "b960f95d-466b-4014-9565-64e51407a364",  # PUR Hartschaum, m³
        "holzfaser":     "ee0c4b18-f9c9-44d1-8766-36db08856a2f",  # Holzfaserdämmstoff flexibel, m³
        "hanf":          "9a9f76b6-54f0-421e-9f8a-6a5db3a22e1d",  # Hanfvlies, m³
        "armier":        "96171066-34d9-4b33-b1e6-3af1ea11db61",  # Zementmörtel (Armierung), m³
        "silikat":       "af98c17b-b748-4d08-b5d5-9ff028ae7f25",  # ≈ Kalkzementmörtel, m³
        "kunstharz":     "5541250a-f8d8-4c67-9f24-47ab54686c30",  # Kunstharzputz, m³
        "kratzputz":     "af98c17b-b748-4d08-b5d5-9ff028ae7f25",  # ≈ Kalkzementmörtel, m³
        "kalk_z_a":      "af98c17b-b748-4d08-b5d5-9ff028ae7f25",  # Kalkzementmörtel (außen), m³
    }

    # Komplette Bodenaufbauten (Bodenplatte inkl. Estrich/Dämmung) mit Bemessungs-U-Werten.
    # Wichtig: Es sind GANZE Aufbauten – nicht Einzelmaterialien. Eine nackte Betonplatte
    # (U ≈ 3,8) führte zuvor zu absurden Heizwärmebedarfen. F_x (Erdreich 0,6 / unbeheizt
    # aus Temperatur) wird zusätzlich im Frontend angewandt.
    FLOOR_PRESETS = {
        4001: {'u_value': 0.15},  # Passivhaus-Bodenplatte (200 mm Dämmung)
        4002: {'u_value': 0.25},  # Neubau gut gedämmt (120 mm)
        4003: {'u_value': 0.35},  # GEG-Referenz (100 mm Dämmung)
        4004: {'u_value': 0.60},  # Altbau leicht gedämmt (50 mm)
        4005: {'u_value': 1.30},  # Altbau ungedämmt (Betonplatte + Estrich)
    }

    # Komplette Dachaufbauten mit realistischen U-Werten (W/m²K)
    # Quelle: GEG 2024 Anforderungen + DIN 4108-2 Standardaufbauten
    ROOF_PRESETS = {
        3001: {'u_value': 0.14},  # Passivhaus-Dach (300 mm Dämmung)
        3002: {'u_value': 0.18},  # Steildach gut gedämmt (200 mm Aufsparren)
        3003: {'u_value': 0.20},  # Flachdach gedämmt (200 mm EPS/PUR)
        3004: {'u_value': 0.24},  # GEG-Mindeststandard Dach (Sanierung)
        3005: {'u_value': 0.45},  # Altbau leicht gedämmt (80 mm)
        3006: {'u_value': 1.20},  # Altbau ungedämmt (nur Ziegeleindeckung)
    }
    
    def get_queryset(self):
        """Filter nach Kategorie wenn parameter 'category' gegeben"""
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_preset_data(self, material_id):
        metadata = self.PRESET_METADATA.get(material_id, {})
        return {
            'id': material_id,
            'name': metadata.get('name', f'ÖKOBAUDAT Material {material_id}'),
            'producer': None,
            'category': metadata.get('category'),
            'u_value': None,
            'embodied_co2': None,
            'notes': None,
        }

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Http404:
            material_id = int(kwargs.get('pk'))
            preset_data = self.get_preset_data(material_id)
            if material_id in self.PRESET_METADATA:
                return Response(preset_data)
            raise

    @action(detail=False, methods=['get'])
    def popular_walls(self, request):
        """Beliebte Wandmaterialien mit einfachen Namen für UI"""
        materials = [
            {'id': 8, 'simple_name': 'Ziegelwand', 'category': 'wall'},
            {'id': 354, 'simple_name': 'Leichtbeton-Block', 'category': 'wall'},
            {'id': 1332, 'simple_name': 'Kalksandstein', 'category': 'wall'},
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
            {'id': 2005, 'simple_name': 'Stahlzarge Innentür (⚠ nicht Außenhülle)', 'category': 'door', **self.DOOR_PRESETS[2005]},
            {'id': 2006, 'simple_name': 'Kunststoff-Nebeneingangstür', 'category': 'door', **self.DOOR_PRESETS[2006]},
            {'id': 2007, 'simple_name': 'Industrie-Sectionaltore', 'category': 'door', **self.DOOR_PRESETS[2007]},
        ]
        return Response(doors)

    @action(detail=True, methods=['get'])
    def thermal_u(self, request, pk=None):
        """Berechnet einen U-Wert aus hinterlegter Lambda-Annahme und Dicke."""
        material = None
        material_id = int(pk)
        try:
            material = self.get_object()
        except Http404:
            # Wenn das Material nicht importiert ist, nutze die Fallback-Presets
            if material_id not in self.PRESET_METADATA:
                return Response({
                    'id': material_id,
                    'name': f'ÖKOBAUDAT Material {material_id}',
                    'u_value': None,
                    'lambda_value': None,
                    'thickness_mm': None,
                    'default_thickness_mm': None,
                    'formula': 'not_available',
                }, status=200)

        if material is None:
            material = type('MaterialStub', (), self.get_preset_data(material_id))()
            material.id = material_id
            material.name = self.PRESET_METADATA.get(material_id, {}).get('name', f'ÖKOBAUDAT Material {material_id}')
            material.u_value = self.WINDOW_PRESETS.get(material_id, {}).get('u_value') if material_id in self.WINDOW_PRESETS else \
                              self.DOOR_PRESETS.get(material_id, {}).get('u_value') if material_id in self.DOOR_PRESETS else None

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

        floor_preset = self.FLOOR_PRESETS.get(material.id)
        if floor_preset:
            return Response({
                'id': material.id,
                'name': material.name,
                'u_value': floor_preset['u_value'],
                'lambda_value': None,
                'thickness_mm': None,
                'default_thickness_mm': None,
                'formula': 'floor_preset',   # kompletter Aufbau, Bemessungs-U
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
    
    @action(detail=False, methods=['post'])
    def wall_gwp(self, request):
        """Graue Emissionen (GWP A1–A3) eines Wandaufbaus aus echten ÖKOBAUDAT-Daten.

        Erwartet: {"layers": [{"material": <Frontend-Schlüssel>, "thickness_mm": <mm>}, …],
                   "wall_area_m2": <optional>}
        Umrechnung je Bezugseinheit des Datensatzes:
          m³  → GWP/m³ · Dicke ;  kg → GWP/kg · Rohdichte · Dicke ;  m² → GWP/m² direkt.
        """
        layers_in = request.data.get('layers', [])
        wall_area = safe_float(request.data.get('wall_area_m2'), 0.0)

        results = []
        total_per_m2 = 0.0
        missing = []
        for layer in layers_in:
            key = str(layer.get('material', '')).strip()
            thickness_m = safe_float(layer.get('thickness_mm'), 0.0) / 1000.0
            # Direkte ÖKOBAUDAT-UUID (aus der Materialsuche) hat Vorrang, sonst
            # Frontend-Schlüssel über die feste Preset-Zuordnung.
            uuid = str(layer.get('uuid', '')).strip() or self.LAYER_OBD_MAP.get(key)
            mat = EkobaudatMaterial.objects.filter(uuid=uuid).first() if uuid else None
            if mat is None or mat.gwp_a1a3 is None:
                missing.append(key or '(leer)')
                # Ergebnis-Eintrag trotzdem anhängen (Reihenfolge 1:1 zu den Eingabe-Schichten,
                # damit das Frontend den Wert je Zeile zuordnen kann).
                results.append({'material': key, 'dataset': None, 'dataset_type': None, 'uuid': uuid or None, 'gwp_per_m2': None})
                continue
            qty = mat.ref_quantity or 1.0
            unit = (mat.ref_unit or '').lower()
            gwp_per_m2 = None
            if unit == 'm3' and thickness_m > 0:
                gwp_per_m2 = (mat.gwp_a1a3 / qty) * thickness_m
            elif unit == 'kg' and thickness_m > 0 and mat.density:
                gwp_per_m2 = (mat.gwp_a1a3 / qty) * mat.density * thickness_m
            elif unit in ('qm', 'm2'):
                gwp_per_m2 = mat.gwp_a1a3 / qty
            if gwp_per_m2 is None:
                missing.append(key)
                results.append({'material': key, 'dataset': mat.name, 'dataset_type': mat.dataset_type, 'uuid': mat.uuid, 'gwp_per_m2': None})
                continue
            total_per_m2 += gwp_per_m2
            results.append({
                'material': key,
                'dataset': mat.name,
                'dataset_type': mat.dataset_type,
                'uuid': mat.uuid,
                'gwp_per_m2': round(gwp_per_m2, 2),
            })

        return Response({
            'layers': results,
            'missing': missing,
            'gwp_per_m2': round(total_per_m2, 2),
            'gwp_total': round(total_per_m2 * wall_area, 1) if wall_area > 0 else None,
            'wall_area_m2': wall_area or None,
            'source': 'ÖKOBAUDAT 2024 (Modul A1–A3)',
        })

    @action(detail=False, methods=['get'])
    def popular_roof(self, request):
        """Beliebte Dach-Aufbauten mit realistischen U-Werten (komplett gedämmt)."""
        materials = [
            {'id': 3001, 'simple_name': 'Passivhaus-Dach (300 mm Dämmung)', 'category': 'roof', **self.ROOF_PRESETS[3001]},
            {'id': 3002, 'simple_name': 'Steildach gedämmt (200 mm Aufsparren)', 'category': 'roof', **self.ROOF_PRESETS[3002]},
            {'id': 3003, 'simple_name': 'Flachdach gedämmt (200 mm EPS/PUR)', 'category': 'roof', **self.ROOF_PRESETS[3003]},
            {'id': 3004, 'simple_name': 'GEG-Mindeststandard (Sanierung)', 'category': 'roof', **self.ROOF_PRESETS[3004]},
            {'id': 3005, 'simple_name': 'Altbau leicht gedämmt (80 mm)', 'category': 'roof', **self.ROOF_PRESETS[3005]},
            {'id': 3006, 'simple_name': 'Altbau ungedämmt', 'category': 'roof', **self.ROOF_PRESETS[3006]},
        ]
        return Response(materials)
    
    @action(detail=False, methods=['get'])
    def popular_floor(self, request):
        """Komplette Boden-Aufbauten mit Bemessungs-U-Werten (wie beim Dach)."""
        materials = [
            {'id': 4001, 'simple_name': 'Passivhaus-Bodenplatte (200 mm Dämmung)', 'category': 'floor', **self.FLOOR_PRESETS[4001]},
            {'id': 4002, 'simple_name': 'Neubau gut gedämmt (120 mm)', 'category': 'floor', **self.FLOOR_PRESETS[4002]},
            {'id': 4003, 'simple_name': 'GEG-Referenz (100 mm Dämmung)', 'category': 'floor', **self.FLOOR_PRESETS[4003]},
            {'id': 4004, 'simple_name': 'Altbau leicht gedämmt (50 mm)', 'category': 'floor', **self.FLOOR_PRESETS[4004]},
            {'id': 4005, 'simple_name': 'Altbau ungedämmt (Betonplatte + Estrich)', 'category': 'floor', **self.FLOOR_PRESETS[4005]},
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