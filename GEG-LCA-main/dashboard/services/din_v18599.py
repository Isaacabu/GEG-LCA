from __future__ import annotations

from typing import Any, Dict, List


ZONE_PROFILE_DEFAULTS = {
    "office": {
        "label": "Büro",
        "air_change_rate": 0.6,
        "internal_gains_density": 4.5,
        "occupancy_hours": 2500,
        "gain_utilization_factor": 0.75,
        "setpoint_temperature": 20.0,
    },
    "living": {
        "label": "Wohnen",
        "air_change_rate": 0.5,
        "internal_gains_density": 3.0,
        "occupancy_hours": 3000,
        "gain_utilization_factor": 0.8,
        "setpoint_temperature": 20.0,
    },
    "meeting": {
        "label": "Besprechung",
        "air_change_rate": 1.0,
        "internal_gains_density": 5.0,
        "occupancy_hours": 1400,
        "gain_utilization_factor": 0.7,
        "setpoint_temperature": 21.0,
    },
    "school": {
        "label": "Schule",
        "air_change_rate": 0.8,
        "internal_gains_density": 4.0,
        "occupancy_hours": 1800,
        "gain_utilization_factor": 0.72,
        "setpoint_temperature": 20.0,
    },
    "circulation": {
        "label": "Flur",
        "air_change_rate": 0.7,
        "internal_gains_density": 1.5,
        "occupancy_hours": 1200,
        "gain_utilization_factor": 0.65,
        "setpoint_temperature": 18.0,
    },
    "service": {
        "label": "Nebenraum",
        "air_change_rate": 0.7,
        "internal_gains_density": 2.0,
        "occupancy_hours": 1600,
        "gain_utilization_factor": 0.68,
        "setpoint_temperature": 19.0,
    },
}


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_non_negative(name: str, value: float, errors: List[str]) -> None:
    if value < 0:
        errors.append(f"{name} darf nicht negativ sein.")


def validate_positive(name: str, value: float, errors: List[str]) -> None:
    if value <= 0:
        errors.append(f"{name} muss groesser als 0 sein.")


def validate_u_value(name: str, value: float, errors: List[str]) -> None:
    if value < 0:
        errors.append(f"{name} darf nicht negativ sein.")
    elif value > 5:
        errors.append(f"{name} ist unrealistisch hoch (> 5 W/m²K).")


def get_rating(value_per_m2a: float) -> Dict[str, str]:
    if value_per_m2a <= 40:
        return {
            "label": "Sehr gut",
            "color": "green",
            "message": "Niedriger Heizwärmebedarf - energetisch günstig."
        }
    if value_per_m2a <= 80:
        return {
            "label": "Mittel",
            "color": "yellow",
            "message": "Akzeptabler Bereich - Optimierung sinnvoll."
        }
    return {
        "label": "Kritisch",
        "color": "red",
        "message": "Hoher Heizwärmebedarf - Gebäudehülle verbessern."
    }


def build_zone_summary(zones: Any) -> Dict[str, Any]:
    if not isinstance(zones, list):
        zones = []

    parsed_zones: List[Dict[str, Any]] = []
    total_area = 0.0
    weighted_air_change = 0.0
    weighted_internal_gains = 0.0
    weighted_occupancy_hours = 0.0
    weighted_gain_utilization = 0.0
    weighted_setpoint = 0.0

    for index, zone in enumerate(zones, start=1):
        if not isinstance(zone, dict):
            continue

        usage_profile = str(zone.get("usage_profile", "office")).strip() or "office"
        defaults = ZONE_PROFILE_DEFAULTS.get(usage_profile, ZONE_PROFILE_DEFAULTS["office"])
        area = safe_float(zone.get("area"))
        if area <= 0:
            continue

        zone_name = str(zone.get("name", f"Zone {index}")).strip() or f"Zone {index}"
        air_change_rate = safe_float(zone.get("air_change_rate"), defaults["air_change_rate"])
        internal_gains_density = safe_float(zone.get("internal_gains_density"), defaults["internal_gains_density"])
        occupancy_hours = safe_float(zone.get("occupancy_hours"), defaults["occupancy_hours"])
        gain_utilization_factor = safe_float(zone.get("gain_utilization_factor"), defaults["gain_utilization_factor"])
        setpoint_temperature = safe_float(zone.get("setpoint_temperature"), defaults["setpoint_temperature"])

        parsed_zones.append({
            "name": zone_name,
            "usage_profile": usage_profile,
            "usage_label": defaults["label"],
            "area": area,
            "air_change_rate": air_change_rate,
            "internal_gains_density": internal_gains_density,
            "occupancy_hours": occupancy_hours,
            "gain_utilization_factor": gain_utilization_factor,
            "setpoint_temperature": setpoint_temperature,
        })

        total_area += area
        weighted_air_change += area * air_change_rate
        weighted_internal_gains += area * internal_gains_density
        weighted_occupancy_hours += area * occupancy_hours
        weighted_gain_utilization += area * gain_utilization_factor
        weighted_setpoint += area * setpoint_temperature

    if total_area <= 0:
        return {
            "count": 0,
            "total_area": 0.0,
            "zones": [],
            "weighted_air_change_rate": None,
            "weighted_internal_gains_density": None,
            "weighted_occupancy_hours": None,
            "weighted_gain_utilization_factor": None,
            "weighted_setpoint_temperature": None,
            "dominant_profile": None,
        }

    dominant_profile = max(parsed_zones, key=lambda zone: zone["area"])["usage_label"] if parsed_zones else None

    return {
        "count": len(parsed_zones),
        "total_area": round(total_area, 2),
        "zones": parsed_zones,
        "weighted_air_change_rate": round(weighted_air_change / total_area, 3),
        "weighted_internal_gains_density": round(weighted_internal_gains / total_area, 2),
        "weighted_occupancy_hours": round(weighted_occupancy_hours / total_area, 2),
        "weighted_gain_utilization_factor": round(weighted_gain_utilization / total_area, 3),
        "weighted_setpoint_temperature": round(weighted_setpoint / total_area, 2),
        "dominant_profile": dominant_profile,
    }


def calculate_envelope_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    bgf = safe_float(data.get("bgf"), 0)
    gradstunden = safe_float(data.get("gradstunden"), 78000)
    room_height = safe_float(data.get("room_height", data.get("floor_height")), 3.0)
    air_change_rate = safe_float(data.get("air_change_rate"), 0.5)
    thermal_bridge_factor = safe_float(data.get("thermal_bridge_factor"), 0.05)
    internal_gains_density = safe_float(data.get("internal_gains_density"), 2.0)
    occupancy_hours = safe_float(data.get("occupancy_hours"), 2500)
    gain_utilization_factor = safe_float(data.get("gain_utilization_factor"), 0.75)
    zone_summary = build_zone_summary(data.get("zones"))

    if zone_summary["count"] > 0:
        air_change_rate = zone_summary["weighted_air_change_rate"] or air_change_rate
        internal_gains_density = zone_summary["weighted_internal_gains_density"] or internal_gains_density
        occupancy_hours = zone_summary["weighted_occupancy_hours"] or occupancy_hours
        gain_utilization_factor = zone_summary["weighted_gain_utilization_factor"] or gain_utilization_factor

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

    errors: List[str] = []

    validate_non_negative("BGF", bgf, errors)
    validate_non_negative("Gradstunden", gradstunden, errors)
    validate_positive("Raumhöhe", room_height, errors)
    validate_non_negative("Luftwechselrate", air_change_rate, errors)
    validate_non_negative("Wärmebrücken-Faktor", thermal_bridge_factor, errors)
    validate_non_negative("Interne Gewinne", internal_gains_density, errors)
    validate_non_negative("Belegungsstunden", occupancy_hours, errors)
    validate_non_negative("Gewinnnutzungsgrad", gain_utilization_factor, errors)

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
        return {"ok": False, "errors": errors}

    volume = safe_float(data.get("volume"), bgf * room_height)
    if volume <= 0:
        volume = bgf * room_height

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
    window_total = window_north_loss + window_south_loss + window_east_loss + window_west_loss

    envelope_transmission_total = wall_total + roof_floor_total + window_total
    ventilation_loss = 0.34 * air_change_rate * volume
    thermal_bridge_loss = envelope_transmission_total * thermal_bridge_factor

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

    internal_gains_kwh = (bgf * internal_gains_density * occupancy_hours) / 1000
    annual_heat_demand_kwh = ((envelope_transmission_total + ventilation_loss + thermal_bridge_loss) * gradstunden) / 1000
    usable_gains_kwh = (solar_gain_kwh + internal_gains_kwh) * gain_utilization_factor
    adjusted_heat_demand_kwh = max(annual_heat_demand_kwh - usable_gains_kwh, 0)
    specific_heat_demand = adjusted_heat_demand_kwh / bgf

    rating = get_rating(specific_heat_demand)

    return {
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
        "envelope_total": round(envelope_transmission_total + ventilation_loss + thermal_bridge_loss, 2),
        "transmission_total": round(envelope_transmission_total, 2),
        "ventilation_loss": round(ventilation_loss, 2),
        "thermal_bridge_loss": round(thermal_bridge_loss, 2),
        "annual_heat_demand_kwh": round(annual_heat_demand_kwh, 2),
        "solar_gain_kwh": round(solar_gain_kwh, 2),
        "internal_gains_kwh": round(internal_gains_kwh, 2),
        "usable_gains_kwh": round(usable_gains_kwh, 2),
        "adjusted_heat_demand_kwh": round(adjusted_heat_demand_kwh, 2),
        "specific_heat_demand": round(specific_heat_demand, 2),
        "rating_label": rating["label"],
        "rating_color": rating["color"],
        "rating_message": rating["message"],
        "zone_count": zone_summary["count"],
        "zone_total_area": zone_summary["total_area"],
        "zone_dominant_profile": zone_summary["dominant_profile"],
        "zone_weighted_air_change_rate": zone_summary["weighted_air_change_rate"],
        "zone_weighted_internal_gains_density": zone_summary["weighted_internal_gains_density"],
        "zone_weighted_occupancy_hours": zone_summary["weighted_occupancy_hours"],
        "zone_weighted_gain_utilization_factor": zone_summary["weighted_gain_utilization_factor"],
        "zone_weighted_setpoint_temperature": zone_summary["weighted_setpoint_temperature"],
        "zones": zone_summary["zones"],
        "calculation_basis": "DIN V 18599 orientierte Rechenstruktur mit Standardannahmen"
    }


def calculate_system_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    heat_demand_net = safe_float(data.get("heat_demand_net"))
    bgf = safe_float(data.get("bgf"))
    heating_system = data.get("heating_system", "gas")
    efficiency = safe_float(data.get("efficiency"), 0.9)
    cop = safe_float(data.get("cop"), 3.5)
    hotwater_demand = safe_float(data.get("hotwater_demand"), 3000)
    auxiliary_electricity = safe_float(data.get("auxiliary_electricity"), 1200)

    errors: List[str] = []

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
        return {"ok": False, "errors": errors}

    primary_factors = {
        "gas": 1.1,
        "heatpump": 1.8,
        "district": 0.7,
        "pellet": 0.2,
    }

    co2_factors = {
        "gas": 0.24,
        "heatpump": 0.40,
        "district": 0.18,
        "pellet": 0.04,
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

    return {
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
        "system_message": system_message,
        "calculation_basis": "DIN V 18599 orientierte Systembewertung mit Standardfaktoren",
    }
