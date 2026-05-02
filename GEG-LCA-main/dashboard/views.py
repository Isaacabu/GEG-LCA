import json
from django.db import transaction
from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import Project, ProjectZone
from .services.din_v18599 import calculate_envelope_profile, calculate_system_profile


def index(request):
    return render(request, "dashboard/index.html")


def _project_to_response(project):
    return {
        "ok": True,
        "project_id": str(project.project_id),
        "project_name": project.project_name,
        "project_number": project.project_number,
        "file_reference": project.file_reference,
        "legal_basis": project.legal_basis,
        "energy_basis": project.energy_basis,
        "building_kind": project.building_kind,
        "location": project.location,
        "payload": project.payload,
        "calculation": project.calculation,
        "zones": [
            {
                "name": zone.zone_name,
                "usage_profile": zone.usage_profile,
                "area": zone.area,
                "setpoint_temperature": zone.setpoint_temperature,
                "air_change_rate": zone.air_change_rate,
                "internal_gains_density": zone.internal_gains_density,
                "occupancy_hours": zone.occupancy_hours,
                "gain_utilization_factor": zone.gain_utilization_factor,
                "payload": zone.payload,
            }
            for zone in project.zones.all().order_by("id")
        ],
    }


def get_rating(value_per_m2a):
    if value_per_m2a <= 40:
        return {
            "label": "Sehr gut",
            "color": "green",
            "message": "Niedriger Heizwärmebedarf – energetisch günstig."
        }
    elif value_per_m2a <= 80:
        return {
            "label": "Mittel",
            "color": "yellow",
            "message": "Akzeptabler Bereich – Optimierung sinnvoll."
        }
    return {
        "label": "Kritisch",
        "color": "red",
        "message": "Hoher Heizwärmebedarf – Gebäudehülle verbessern."
    }


def validate_non_negative(name, value, errors):
    if value < 0:
        errors.append(f"{name} darf nicht negativ sein.")


def validate_u_value(name, value, errors):
    if value < 0:
        errors.append(f"{name} darf nicht negativ sein.")
    elif value > 5:
        errors.append(f"{name} ist unrealistisch hoch (> 5 W/m²K).")


def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@csrf_exempt
def calculate(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)

    try:
        profile = calculate_envelope_profile(json.loads(request.body))
        if not profile.get("ok"):
            return JsonResponse(profile, status=400)
        return JsonResponse(profile)

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
        profile = calculate_system_profile(json.loads(request.body))
        if not profile.get("ok"):
            return JsonResponse(profile, status=400)
        return JsonResponse(profile)

    except Exception as e:
        return JsonResponse({
            "ok": False,
            "errors": [f"Unerwarteter Fehler: {str(e)}"]
        }, status=500)


@csrf_exempt
def save_project(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Only POST allowed"}, status=400)

    try:
        data = json.loads(request.body)
        project_data = data.get("project", {})
        calculation_data = data.get("calculation", {})
        zones_data = data.get("zones", [])

        project_name = project_data.get("project_name") or "Unbenanntes Projekt"

        with transaction.atomic():
            project_id = project_data.get("project_id")
            if project_id:
                project = Project.objects.filter(project_id=project_id).first()
            else:
                project = None

            if project is None:
                project = Project.objects.create(
                    project_name=project_name,
                    project_number=project_data.get("project_number", ""),
                    file_reference=project_data.get("file_reference", ""),
                    legal_basis=project_data.get("legal_basis", ""),
                    energy_basis=project_data.get("energy_basis", ""),
                    building_kind=project_data.get("building_kind", ""),
                    location=project_data.get("location", ""),
                    payload=data,
                    calculation=calculation_data,
                )
            else:
                project.project_name = project_name
                project.project_number = project_data.get("project_number", "")
                project.file_reference = project_data.get("file_reference", "")
                project.legal_basis = project_data.get("legal_basis", "")
                project.energy_basis = project_data.get("energy_basis", "")
                project.building_kind = project_data.get("building_kind", "")
                project.location = project_data.get("location", "")
                project.payload = data
                project.calculation = calculation_data
                project.save()
                project.zones.all().delete()

            for zone_data in zones_data:
                if not isinstance(zone_data, dict):
                    continue
                ProjectZone.objects.create(
                    project=project,
                    zone_name=zone_data.get("name", "Zone"),
                    usage_profile=zone_data.get("usage_profile", "office"),
                    area=safe_float(zone_data.get("area")),
                    setpoint_temperature=safe_float(zone_data.get("setpoint_temperature")),
                    air_change_rate=safe_float(zone_data.get("air_change_rate")),
                    internal_gains_density=safe_float(zone_data.get("internal_gains_density")),
                    occupancy_hours=safe_float(zone_data.get("occupancy_hours")),
                    gain_utilization_factor=safe_float(zone_data.get("gain_utilization_factor")),
                    payload=zone_data,
                )

        return JsonResponse(_project_to_response(project))

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@csrf_exempt
def load_project(request, project_id):
    if request.method != "GET":
        return JsonResponse({"ok": False, "error": "Only GET allowed"}, status=400)

    project = get_object_or_404(Project, project_id=project_id)
    return JsonResponse(_project_to_response(project))


def project_report(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)
    zones = project.zones.all().order_by("id")
    return render(request, "dashboard/report.html", {
        "project": project,
        "zones": zones,
        "calculation": project.calculation,
    })