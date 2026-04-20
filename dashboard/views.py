import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def index(request):
    return render(request, "dashboard/index.html")


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
        data = json.loads(request.body)

        bgf = safe_float(data.get("bgf"), 0)
        gradstunden = safe_float(data.get("gradstunden"), 78000)

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
        g_value = safe_float(data.get("g_value"), 0.55)

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

        if g_value < 0 or g_value > 1:
            errors.append("g-Wert muss zwischen 0 und 1 liegen.")

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

        solar_factor_north = 20
        solar_factor_south = 90
        solar_factor_east = 50
        solar_factor_west = 50

        solar_gain_kwh = (
            window_north_area * g_value * solar_factor_north
            + window_south_area * g_value * solar_factor_south
            + window_east_area * g_value * solar_factor_east
            + window_west_area * g_value * solar_factor_west
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
        efficiency = safe_float(data.get("efficiency"), 0.9)
        cop = safe_float(data.get("cop"), 3.5)

        hotwater_demand = safe_float(data.get("hotwater_demand"), 3000)
        auxiliary_electricity = safe_float(data.get("auxiliary_electricity"), 1200)

        errors = []

        validate_non_negative("Heizwärmebedarf netto", heat_demand_net, errors)
        validate_non_negative("BGF", bgf, errors)
        validate_non_negative("Warmwasserbedarf", hotwater_demand, errors)
        validate_non_negative("Hilfsstrom", auxiliary_electricity, errors)

        if bgf == 0:
            errors.append("BGF darf nicht 0 sein.")

        valid_systems = ["gas", "heatpump", "district", "pellet"]
        if heating_system not in valid_systems:
            errors.append("Ungültiges Heizsystem.")

        if efficiency <= 0 or efficiency > 1.2:
            errors.append("Wirkungsgrad muss > 0 und plausibel sein (z. B. 0.85 bis 1.0).")

        if cop <= 0 or cop > 10:
            errors.append("COP muss > 0 und plausibel sein (z. B. 2.5 bis 5.0).")

        if errors:
            return JsonResponse({"ok": False, "errors": errors}, status=400)

        # Faktoren
        primary_factors = {
            "gas": 1.1,
            "heatpump": 1.8,
            "district": 0.7,
            "pellet": 0.2
        }

        co2_factors = {
            "gas": 0.24,
            "heatpump": 0.40,
            "district": 0.18,
            "pellet": 0.04
        }

        if heating_system == "heatpump":
            heating_end_energy = heat_demand_net / cop
            hotwater_end_energy = hotwater_demand / cop
        else:
            heating_end_energy = heat_demand_net / efficiency
            hotwater_end_energy = hotwater_demand / efficiency

        total_end_energy = heating_end_energy + hotwater_end_energy + auxiliary_electricity

        primary_energy = total_end_energy * primary_factors[heating_system]
        co2_emissions = total_end_energy * co2_factors[heating_system]

        specific_end_energy = total_end_energy / bgf
        specific_primary_energy = primary_energy / bgf

        # einfache Bewertung
        if specific_primary_energy <= 60:
            system_label = "Sehr effizient"
            system_color = "green"
            system_message = "Die Anlagentechnik arbeitet energetisch günstig."
        elif specific_primary_energy <= 120:
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