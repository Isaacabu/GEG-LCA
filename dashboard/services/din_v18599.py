"""
Energiebilanz-Engine nach DIN V 18599-2 / DIN EN ISO 13790.

Kernfunktionen:
- calculate_envelope_profile(): Heizwärmebedarf via Monatsbilanzverfahren
  mit dynamischem Gewinnnutzungsgrad η(γ, τ).
- calculate_system_profile(): Anlagentechnik mit GEG-2024 Faktoren
  (End-, Primärenergie, CO2, nicht erneuerbarer Anteil, PV-Eigenverbrauch).
- calculate_reference_building(): GEG-Referenzgebäude (Anlage 1) als Soll-Wert.

Backward Compatibility:
Alle bislang vom Frontend erwarteten Feldnamen werden weiterhin geliefert
(annual_heat_demand_kwh, adjusted_heat_demand_kwh, specific_heat_demand,
rating_*, system_*, primary_energy, specific_primary_energy, ...).
Neue Felder werden ergänzt (monthly_balance, eta_gain_utilization,
non_renewable_primary_energy, geg_reference_comparison, ...).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..utils import safe_float, validate_non_negative, validate_positive, validate_u_value, get_rating
from ..constants import (
    SOLAR_FACTORS, MONTHLY_SOLAR_RADIATION,
    CLIMATE_LOCATIONS, DEFAULT_CLIMATE_LOCATION,
    DEFAULT_INDOOR_SETPOINT, HEATING_LIMIT_TEMPERATURE,
    PRIMARY_ENERGY_FACTORS, NREN_PRIMARY_FACTORS, CO2_FACTORS,
    SYSTEM_RATING_THRESHOLDS,
    DEFAULT_GRADSTUNDEN, DEFAULT_G_VALUE, VALID_HEATING_SYSTEMS,
    DEFAULT_HOTWATER_DEMAND, DEFAULT_HOTWATER_DEMAND_PER_M2,
    DEFAULT_AUXILIARY_ELECTRICITY,
    DEFAULT_ROOM_HEIGHT, VENTILATION_CONSTANT, DEFAULT_AIR_CHANGE_RATE,
    DEFAULT_HEAT_RECOVERY,
    DEFAULT_THERMAL_BRIDGE_FACTOR,
    DEFAULT_INTERNAL_GAINS_DENSITY, DEFAULT_OCCUPANCY_HOURS,
    DEFAULT_GAIN_UTILIZATION_FACTOR,
    FRAME_FACTOR_FF, SHADING_FACTOR_FS_DEFAULT, DIRT_FACTOR_FW,
    NON_PERPENDICULAR_CORRECTION,
    DEFAULT_EFFICIENCY, DEFAULT_COP, DEFAULT_COP_HOTWATER,
    MAX_EFFICIENCY, MAX_COP, MAX_G_VALUE, MIN_G_VALUE,
    THERMAL_MASS_CLASSES, DEFAULT_THERMAL_MASS_CLASS,
    HOURS_PER_MONTH, MONTH_LABELS,
    GEG_REFERENCE_U_VALUES, GEG_REFERENCE_PRIMARY_LIMIT,
    USAGE_PROFILES, USAGE_VARIANT_OVERRIDES,
    OCCUPANT_HEAT_OUTPUT_W, DEFAULT_PERSONENDICHTE_M2_PER_PERSON,
    STATE_TO_CLIMATE, CITY_TO_CLIMATE,
    ELEVATION_LAPSE_RATE_K_PER_M, REFERENCE_ELEVATION_M,
)


# =============================================================================
# NUTZUNGSPROFIL- & KLIMA-AUFLÖSUNG (aus Frontend-Eingaben)
# =============================================================================
def _resolve_usage_profile(building_type: str, variant: str) -> Dict[str, Any]:
    """Liefert die Nutzungsrandbedingungen für gegebenen Gebäudetyp/-Variante."""
    base_key = (building_type or 'wohngebaeude').strip().lower()
    base = dict(USAGE_PROFILES.get(base_key, USAGE_PROFILES['wohngebaeude']))
    override = USAGE_VARIANT_OVERRIDES.get((variant or '').strip())
    if override:
        base.update(override)
    base['_key'] = base_key
    return base


def _resolve_climate_key(climate_location: str, state: str, city: str) -> str:
    """Bestimmt den TRY-Klimadatensatz aus Frontend-Auswahl."""
    if climate_location:
        key = climate_location.strip().lower()
        if key in CLIMATE_LOCATIONS:
            return key
    if city and city.strip() in CITY_TO_CLIMATE:
        return CITY_TO_CLIMATE[city.strip()]
    if state and state.strip() in STATE_TO_CLIMATE:
        return STATE_TO_CLIMATE[state.strip()]
    return DEFAULT_CLIMATE_LOCATION


# =============================================================================
# ZONEN-PROFILE (DIN V 18599-10 Tabelle Nutzungsrandbedingungen, vereinfacht)
# =============================================================================
ZONE_PROFILE_DEFAULTS = {
    "office":      {"label": "Büro",        "air_change_rate": 0.6, "internal_gains_density": 4.5, "occupancy_hours": 2500, "gain_utilization_factor": 0.75, "setpoint_temperature": 20.0},
    "living":      {"label": "Wohnen",      "air_change_rate": 0.5, "internal_gains_density": 3.0, "occupancy_hours": 8760, "gain_utilization_factor": 0.80, "setpoint_temperature": 20.0},
    "meeting":     {"label": "Besprechung", "air_change_rate": 1.0, "internal_gains_density": 5.0, "occupancy_hours": 1400, "gain_utilization_factor": 0.70, "setpoint_temperature": 21.0},
    "school":      {"label": "Schule",      "air_change_rate": 0.8, "internal_gains_density": 4.0, "occupancy_hours": 1800, "gain_utilization_factor": 0.72, "setpoint_temperature": 20.0},
    "circulation": {"label": "Flur",        "air_change_rate": 0.7, "internal_gains_density": 1.5, "occupancy_hours": 1200, "gain_utilization_factor": 0.65, "setpoint_temperature": 18.0},
    "service":     {"label": "Nebenraum",   "air_change_rate": 0.7, "internal_gains_density": 2.0, "occupancy_hours": 1600, "gain_utilization_factor": 0.68, "setpoint_temperature": 19.0},
}


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================
def _round(value: Any, digits: int = 2) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _get_climate(location_key: Optional[str]) -> Dict[str, Any]:
    """Liefert Klimadatensatz; fällt auf Potsdam zurück, falls unbekannt."""
    key = (location_key or DEFAULT_CLIMATE_LOCATION).lower().strip()
    return CLIMATE_LOCATIONS.get(key, CLIMATE_LOCATIONS[DEFAULT_CLIMATE_LOCATION])


def _gain_utilization_factor(gamma: float, tau_h: float) -> float:
    """
    Dynamischer Gewinnnutzungsgrad η_gn nach DIN EN ISO 13790, Abschnitt 12.

        η = (1 - γ^a) / (1 - γ^(a+1))   für γ ≠ 1
        η = a / (a + 1)                 für γ = 1
        a = a0 + τ / τ0    (a0 = 1.0, τ0 = 15 h für Heizfall)

    γ = Q_gains / Q_losses (Gewinn-/Verlust-Verhältnis)
    τ = Zeitkonstante des Gebäudes (h) = C_m / H_tot
    """
    a0, tau0 = 1.0, 15.0
    a = a0 + (max(tau_h, 0.1) / tau0)

    if gamma <= 0:
        return 1.0
    if abs(gamma - 1.0) < 1e-6:
        return a / (a + 1.0)
    try:
        return (1.0 - gamma ** a) / (1.0 - gamma ** (a + 1.0))
    except (OverflowError, ZeroDivisionError):
        return 1.0 if gamma < 1 else 0.0


def build_zone_summary(zones: Any) -> Dict[str, Any]:
    """Aggregiert Mehrzonen-Eingaben flächengewichtet (Vorab-Mittelung)."""
    if not isinstance(zones, list):
        zones = []

    parsed_zones: List[Dict[str, Any]] = []
    total_area = 0.0
    sums = {k: 0.0 for k in ("air_change", "gains", "occ", "util", "setp")}

    for index, zone in enumerate(zones, start=1):
        if not isinstance(zone, dict):
            continue
        usage_profile = str(zone.get("usage_profile", "office")).strip() or "office"
        defaults = ZONE_PROFILE_DEFAULTS.get(usage_profile, ZONE_PROFILE_DEFAULTS["office"])
        area = safe_float(zone.get("area"))
        if area <= 0:
            continue

        zone_name = str(zone.get("name", f"Zone {index}")).strip() or f"Zone {index}"
        acr = safe_float(zone.get("air_change_rate"), defaults["air_change_rate"])
        igd = safe_float(zone.get("internal_gains_density"), defaults["internal_gains_density"])
        occ = safe_float(zone.get("occupancy_hours"), defaults["occupancy_hours"])
        guf = safe_float(zone.get("gain_utilization_factor"), defaults["gain_utilization_factor"])
        sp  = safe_float(zone.get("setpoint_temperature"), defaults["setpoint_temperature"])

        parsed_zones.append({
            "name": zone_name, "usage_profile": usage_profile, "usage_label": defaults["label"],
            "area": area, "air_change_rate": acr, "internal_gains_density": igd,
            "occupancy_hours": occ, "gain_utilization_factor": guf, "setpoint_temperature": sp,
        })
        total_area += area
        sums["air_change"] += area * acr
        sums["gains"]      += area * igd
        sums["occ"]        += area * occ
        sums["util"]       += area * guf
        sums["setp"]       += area * sp

    if total_area <= 0:
        return {"count": 0, "total_area": 0.0, "zones": [],
                "weighted_air_change_rate": None, "weighted_internal_gains_density": None,
                "weighted_occupancy_hours": None, "weighted_gain_utilization_factor": None,
                "weighted_setpoint_temperature": None, "dominant_profile": None}

    dom = max(parsed_zones, key=lambda z: z["area"])["usage_label"]
    return {
        "count": len(parsed_zones), "total_area": round(total_area, 2), "zones": parsed_zones,
        "weighted_air_change_rate":          round(sums["air_change"] / total_area, 3),
        "weighted_internal_gains_density":   round(sums["gains"]      / total_area, 2),
        "weighted_occupancy_hours":          round(sums["occ"]        / total_area, 2),
        "weighted_gain_utilization_factor":  round(sums["util"]       / total_area, 3),
        "weighted_setpoint_temperature":     round(sums["setp"]       / total_area, 2),
        "dominant_profile": dom,
    }


# =============================================================================
# HÜLLEN-/HEIZWÄRMEBEDARF (Monatsbilanz nach DIN EN ISO 13790)
# =============================================================================
def _extract_envelope_inputs(data: Dict[str, Any]) -> Dict[str, Any]:
    """Holt und normalisiert alle Hüllen-Eingaben.
    
    Wendet Nutzungsprofil-Defaults (Wohngebäude / Nichtwohngebäude + Variante)
    auf alle Felder an, für die der Aufrufer keinen expliziten Wert geliefert hat.
    """
    # ----- Nutzungsprofil aus Gebäudetyp ableiten -----
    building_type    = str(data.get("building_type", "wohngebaeude") or "wohngebaeude").strip().lower()
    building_variant = str(data.get("building_type_variant", "") or "").strip()
    profile = _resolve_usage_profile(building_type, building_variant)

    # Helfer: explizit gesetzter Wert (> 0 oder vorhanden) sonst Profil-Default
    def _val(key: str, profile_key: str, fallback: float) -> float:
        raw = data.get(key)
        if raw in (None, "", "null"):
            return float(profile.get(profile_key, fallback))
        v = safe_float(raw, 0)
        return v if v > 0 else float(profile.get(profile_key, fallback))

    air_change_rate = _val("air_change_rate", "air_change_rate", DEFAULT_AIR_CHANGE_RATE)
    heat_recovery   = min(0.95, max(0.0, safe_float(
        data.get("heat_recovery", profile.get("heat_recovery", DEFAULT_HEAT_RECOVERY)),
        profile.get("heat_recovery", DEFAULT_HEAT_RECOVERY))))
    setpoint        = _val("setpoint_temperature", "setpoint_temperature", DEFAULT_INDOOR_SETPOINT)
    if setpoint == 0:
        setpoint = profile.get("setpoint_temperature", DEFAULT_INDOOR_SETPOINT)
    occupancy_hours = _val("occupancy_hours", "occupancy_hours", DEFAULT_OCCUPANCY_HOURS)

    bgf = safe_float(data.get("bgf"), 0)

    # ----- Personendichte → interne Gewinne -----
    personendichte = safe_float(
        data.get("personendichte"),
        profile.get("personendichte", DEFAULT_PERSONENDICHTE_M2_PER_PERSON),
    )
    if personendichte <= 0:
        personendichte = profile.get("personendichte", DEFAULT_PERSONENDICHTE_M2_PER_PERSON)

    n_persons = bgf / personendichte if (bgf > 0 and personendichte > 0) else 0.0
    equipment_gains = float(profile.get("equipment_gains", 0.0))
    lighting_gains  = float(profile.get("lighting_gains", 0.0))

    # Q_int,density [W/m²] = (n_persons × P_person + (P_equip + P_light) × BGF) / BGF
    if bgf > 0:
        internal_gains_density_calc = (
            (n_persons * OCCUPANT_HEAT_OUTPUT_W) / bgf
            + equipment_gains + lighting_gains
        )
    else:
        internal_gains_density_calc = DEFAULT_INTERNAL_GAINS_DENSITY

    # Wenn das Frontend einen expliziten internal_gains_density-Wert sendet → der gewinnt
    explicit_igd = data.get("internal_gains_density")
    if explicit_igd in (None, "", "null"):
        internal_gains_density = internal_gains_density_calc
    else:
        internal_gains_density = safe_float(explicit_igd, internal_gains_density_calc)

    # ----- Klima auflösen (climate_location → Stadt → Bundesland) -----
    climate_key = _resolve_climate_key(
        str(data.get("climate_location", "") or ""),
        str(data.get("project_state", "") or data.get("climate_state", "") or ""),
        str(data.get("project_city",  "") or data.get("climate_city",  "") or ""),
    )

    return {
        "bgf": bgf,
        "room_height": safe_float(data.get("room_height", data.get("floor_height")), DEFAULT_ROOM_HEIGHT),
        "volume_override": safe_float(data.get("volume"), 0),
        "elevation_m": safe_float(data.get("elevation_m"), 0),
        "air_change_rate": air_change_rate,
        "heat_recovery": heat_recovery,
        "thermal_bridge_factor": safe_float(data.get("thermal_bridge_factor"), DEFAULT_THERMAL_BRIDGE_FACTOR),
        "thermal_mass_class": str(data.get("thermal_mass_class", DEFAULT_THERMAL_MASS_CLASS)).strip() or DEFAULT_THERMAL_MASS_CLASS,
        "internal_gains_density": internal_gains_density,
        "occupancy_hours": occupancy_hours,
        "setpoint": setpoint,
        "climate_location": climate_key,
        # Nutzung
        "building_type": building_type,
        "building_type_variant": building_variant,
        "usage_label": profile.get("label", ""),
        "personendichte": personendichte,
        "n_persons": n_persons,
        "equipment_gains_density": equipment_gains,
        "lighting_gains_density": lighting_gains,
        "gain_utilization_factor_profile": float(profile.get("gain_utilization_factor", DEFAULT_GAIN_UTILIZATION_FACTOR)),
        # Opake Bauteile
        "walls": {
            'north': (safe_float(data.get("north_area")), safe_float(data.get("north_u"))),
            'south': (safe_float(data.get("south_area")), safe_float(data.get("south_u"))),
            'east':  (safe_float(data.get("east_area")),  safe_float(data.get("east_u"))),
            'west':  (safe_float(data.get("west_area")),  safe_float(data.get("west_u"))),
        },
        "roof":  (safe_float(data.get("roof_area")),  safe_float(data.get("roof_u"))),
        "floor": (safe_float(data.get("floor_area")), safe_float(data.get("floor_u"))),
        # Fenster
        "windows": {
            'north': safe_float(data.get("window_north_area")),
            'south': safe_float(data.get("window_south_area")),
            'east':  safe_float(data.get("window_east_area")),
            'west':  safe_float(data.get("window_west_area")),
        },
        "window_u": safe_float(data.get("window_u")),
        "g_value": safe_float(data.get("g_value"), DEFAULT_G_VALUE),
        "frame_factor": safe_float(data.get("frame_factor"), FRAME_FACTOR_FF),
        "shading_factor": safe_float(data.get("shading_factor"), SHADING_FACTOR_FS_DEFAULT),
        # Türen
        "door_counts": {
            'north': safe_float(data.get("door_north_count"), 0),
            'south': safe_float(data.get("door_south_count"), 0),
            'east':  safe_float(data.get("door_east_count"), 0),
            'west':  safe_float(data.get("door_west_count"), 0),
        },
        "door_area_per_unit": safe_float(data.get("door_area_per_unit"), 2.0),
        "door_u": safe_float(data.get("door_u")),
    }


def _validate_envelope_inputs(p: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    validate_non_negative("BGF", p["bgf"], errors)
    validate_positive("Raumhöhe", p["room_height"], errors)
    validate_non_negative("Luftwechselrate", p["air_change_rate"], errors)
    validate_non_negative("Wärmebrücken-Faktor", p["thermal_bridge_factor"], errors)

    for direction, (area, u) in p["walls"].items():
        validate_non_negative(f"{direction.capitalize()} Fläche", area, errors)
        validate_u_value(f"{direction.capitalize()} U-Wert", u, errors)

    validate_non_negative("Dachfläche", p["roof"][0], errors)
    validate_u_value("Dach U-Wert", p["roof"][1], errors)
    validate_non_negative("Bodenfläche", p["floor"][0], errors)
    validate_u_value("Boden U-Wert", p["floor"][1], errors)

    for direction, area in p["windows"].items():
        validate_non_negative(f"Fenster {direction}", area, errors)
    validate_u_value("Fenster U-Wert", p["window_u"], errors)

    if p["g_value"] < MIN_G_VALUE or p["g_value"] > MAX_G_VALUE:
        errors.append(f"g-Wert muss zwischen {MIN_G_VALUE} und {MAX_G_VALUE} liegen.")
    if p["bgf"] == 0:
        errors.append("BGF darf nicht 0 sein.")
    return errors


def calculate_envelope_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Heizwärmebedarf via Monatsbilanzverfahren nach DIN EN ISO 13790 §7
    mit dynamischem Gewinnnutzungsgrad nach §12.

    Berechnungsablauf je Monat m:
      H_T   = Σ U_i·A_i + ΔU_WB·A_Hüll                 [W/K]   Transmission
      H_V   = ρ·c · n · V · (1 − η_WRG)                [W/K]   Lüftung
      Q_L,m = (H_T + H_V) · (θ_int − θ_e,m) · t_m       [Wh]    Verluste
      Q_G,m = Q_int,m + Q_sol,m                         [Wh]    Gewinne
      γ_m   = Q_G,m / Q_L,m
      η_m   = f(γ_m, τ)
      Q_h,m = max(Q_L,m − η_m · Q_G,m, 0)

    Jahresheizwärmebedarf = Σ Q_h,m
    """
    p = _extract_envelope_inputs(data)
    zone_summary = build_zone_summary(data.get("zones"))

    # Zonen-Mittelwerte überschreiben Defaults (falls Zonen definiert)
    if zone_summary["count"] > 0:
        p["air_change_rate"] = zone_summary["weighted_air_change_rate"] or p["air_change_rate"]
        p["internal_gains_density"] = zone_summary["weighted_internal_gains_density"] or p["internal_gains_density"]
        p["occupancy_hours"] = zone_summary["weighted_occupancy_hours"] or p["occupancy_hours"]
        p["setpoint"] = zone_summary["weighted_setpoint_temperature"] or p["setpoint"]

    errors = _validate_envelope_inputs(p)
    if errors:
        return {"ok": False, "errors": errors}

    # ===== Geometrie =====
    bgf = p["bgf"]
    volume = p["volume_override"] if p["volume_override"] > 0 else bgf * p["room_height"]

    # ===== Türenflächen aus Anzahl =====
    door_areas = {d: cnt * p["door_area_per_unit"] for d, cnt in p["door_counts"].items()}

    # ===== Transmissionswärmeverluste H_T [W/K] =====
    # Wandflächen kommen als Bruttofläche (inkl. Fenster/Türöffnungen) vom Frontend.
    # Nettoabzug: damit Fenster/Türen nicht doppelt gezählt werden.
    wall_losses = {
        d: max(0.0, a - p["windows"].get(d, 0.0) - door_areas.get(d, 0.0)) * u
        for d, (a, u) in p["walls"].items()
    }
    wall_total = sum(wall_losses.values())
    roof_loss = p["roof"][0] * p["roof"][1]
    floor_loss = p["floor"][0] * p["floor"][1]
    window_losses = {d: a * p["window_u"] for d, a in p["windows"].items()}
    window_total = sum(window_losses.values())
    door_losses = {d: a * p["door_u"] for d, a in door_areas.items()}
    door_total = sum(door_losses.values())

    transmission_total = wall_total + roof_loss + floor_loss + window_total + door_total

    # Wärmebrücken: ΔU_WB · A_Hüll  (DIN V 4108-6)
    # Wände als Bruttofläche — Fenster/Türen sind darin enthalten, daher NICHT extra addieren.
    total_envelope_area = (
        sum(a for a, _ in p["walls"].values())
        + p["roof"][0] + p["floor"][0]
    )
    thermal_bridge_loss = p["thermal_bridge_factor"] * total_envelope_area

    H_T = transmission_total + thermal_bridge_loss

    # ===== Lüftungswärmeverlust H_V [W/K] =====
    n_eff = p["air_change_rate"] * (1.0 - p["heat_recovery"])
    H_V = VENTILATION_CONSTANT * n_eff * volume

    H_tot = H_T + H_V  # gesamter Wärmeverlustkoeffizient

    # ===== Zeitkonstante τ (h) für dynamisches η =====
    C_m_spec = THERMAL_MASS_CLASSES.get(p["thermal_mass_class"], THERMAL_MASS_CLASSES[DEFAULT_THERMAL_MASS_CLASS])
    C_m = C_m_spec * bgf  # Wh/K
    tau_h = C_m / H_tot if H_tot > 0 else 100.0

    # ===== Interne Gewinne (kontinuierlich, kWh pro Monat) =====
    # P_int = internal_gains_density [W/m²] · BGF; Energie/Monat = P_int · t_m / 1000
    internal_gain_power_w = p["internal_gains_density"] * bgf
    monthly_internal_gains_kwh = [
        internal_gain_power_w * HOURS_PER_MONTH[m] / 1000.0 for m in range(12)
    ]
    annual_internal_gains_kwh = sum(monthly_internal_gains_kwh)

    # ===== Solare Gewinne je Monat & Orientierung =====
    # Q_sol = Σ A_W,j · g_⊥ · F_F · F_S · F_W · F_⊥ · I_S,j,m
    solar_correction = (
        p["g_value"] * p["frame_factor"] * p["shading_factor"]
        * DIRT_FACTOR_FW * NON_PERPENDICULAR_CORRECTION
    )
    monthly_solar_gains_kwh: List[float] = []
    for m in range(12):
        q = 0.0
        for direction, area in p["windows"].items():
            q += area * solar_correction * MONTHLY_SOLAR_RADIATION[direction][m]
        monthly_solar_gains_kwh.append(q)
    annual_solar_gains_kwh = sum(monthly_solar_gains_kwh)

    # ===== Klimadaten / Monatsbilanz =====
    climate = _get_climate(p["climate_location"])
    monthly_temps = list(climate["monthly_temps"])
    # Höhenlagen-Korrektur (0,65 K pro 100 m über Referenzhöhe)
    elevation_delta_k = 0.0
    if p["elevation_m"] > 0:
        elevation_delta_k = ELEVATION_LAPSE_RATE_K_PER_M * (p["elevation_m"] - REFERENCE_ELEVATION_M)
        monthly_temps = [t - elevation_delta_k for t in monthly_temps]
    theta_int = p["setpoint"]

    monthly_balance: List[Dict[str, Any]] = []
    annual_losses_kwh = 0.0
    annual_heat_demand_monthly_kwh = 0.0

    for m in range(12):
        theta_e = monthly_temps[m]
        # Heizung nur, wenn Außentemp < Heizgrenze (vereinfachtes Kriterium)
        if theta_e >= HEATING_LIMIT_TEMPERATURE:
            losses_kwh = 0.0
            gains_kwh = monthly_internal_gains_kwh[m] + monthly_solar_gains_kwh[m]
            gamma = float('inf') if losses_kwh == 0 else gains_kwh / losses_kwh
            eta = 0.0
            heat_demand_kwh = 0.0
            heating = False
        else:
            delta_T = max(theta_int - theta_e, 0.0)
            hours = HOURS_PER_MONTH[m]
            losses_kwh = H_tot * delta_T * hours / 1000.0
            gains_kwh = monthly_internal_gains_kwh[m] + monthly_solar_gains_kwh[m]
            gamma = gains_kwh / losses_kwh if losses_kwh > 0 else 0.0
            eta = _gain_utilization_factor(gamma, tau_h)
            heat_demand_kwh = max(losses_kwh - eta * gains_kwh, 0.0)
            heating = True

        annual_losses_kwh += losses_kwh
        annual_heat_demand_monthly_kwh += heat_demand_kwh

        monthly_balance.append({
            "month": MONTH_LABELS[m],
            "theta_e": round(theta_e, 1),
            "delta_T": round(max(theta_int - theta_e, 0.0), 1),
            "losses_kwh": round(losses_kwh, 1),
            "internal_gains_kwh": round(monthly_internal_gains_kwh[m], 1),
            "solar_gains_kwh": round(monthly_solar_gains_kwh[m], 1),
            "gamma": round(gamma, 3) if gamma != float('inf') else None,
            "eta_gn": round(eta, 3),
            "heat_demand_kwh": round(heat_demand_kwh, 1),
            "heating": heating,
        })

    usable_gains_kwh = annual_losses_kwh - annual_heat_demand_monthly_kwh

    # ===== Vereinfachte Jahresenergiebilanz (Gradstunden-Methode) =====
    # Vollständige Verlust- und Gewinnseite, damit das Ergebnis konsistent zur
    # Monatsbilanz ist (frühere Version ignorierte H_V und Q_int → ca. +200 %).
    #   Q_L,brutto = (H_T + H_V) × Gradstunden / 1000              [kWh/a]
    #   Q_int_a    = q_int [W/m²] × BGF × 8760 / 1000              [kWh/a]
    #   Q_sol      = Σ A_win × g × SOLAR_FACTORS[direction]        [kWh/a]
    #   Q_h,netto  = max(Q_L,brutto - η × (Q_int_a + Q_sol), 0)
    gradstunden = safe_float(data.get("gradstunden"), DEFAULT_GRADSTUNDEN)
    solar_gain_simplified_kwh = sum(
        area * p["g_value"] * SOLAR_FACTORS[direction]
        for direction, area in p["windows"].items()
    )
    # Brutto = ALLE Verluste (Transmission inkl. WB + Lüftung), nicht nur Hülle
    annual_heat_demand_kwh = H_tot * gradstunden / 1000
    # Vereinfachter Gewinnnutzungsgrad aus Nutzungsprofil (oder Default)
    eta_simplified = p.get("gain_utilization_factor_profile", DEFAULT_GAIN_UTILIZATION_FACTOR)
    internal_gains_annual_kwh = p["internal_gains_density"] * bgf * 8760 / 1000.0
    total_gains_simplified_kwh = internal_gains_annual_kwh + solar_gain_simplified_kwh
    adjusted_heat_demand_kwh = max(
        annual_heat_demand_kwh - eta_simplified * total_gains_simplified_kwh,
        0.0,
    )
    specific_heat_demand = adjusted_heat_demand_kwh / bgf if bgf > 0 else 0.0
    rating = get_rating(specific_heat_demand)

    # envelope_total = reine Transmissionswärmeverluste (Gebäudehülle, ohne Lüftung)
    envelope_total_wk = transmission_total

    return {
        "ok": True,
        # ----- Einzelverluste opake Bauteile (Legacy-Format) -----
        "north_loss":  _round(wall_losses['north']),
        "south_loss":  _round(wall_losses['south']),
        "east_loss":   _round(wall_losses['east']),
        "west_loss":   _round(wall_losses['west']),
        "wall_total":  _round(wall_total),
        "roof_loss":   _round(roof_loss),
        "floor_loss":  _round(floor_loss),
        "roof_floor_total": _round(roof_loss + floor_loss),
        # ----- Fenster & Türen (Legacy) -----
        "window_north_loss": _round(window_losses['north']),
        "window_south_loss": _round(window_losses['south']),
        "window_east_loss":  _round(window_losses['east']),
        "window_west_loss":  _round(window_losses['west']),
        "window_total": _round(window_total),
        "door_north_loss": _round(door_losses['north']),
        "door_south_loss": _round(door_losses['south']),
        "door_east_loss":  _round(door_losses['east']),
        "door_west_loss":  _round(door_losses['west']),
        "door_total": _round(door_total),
        # ----- Aggregierte Verlustkoeffizienten -----
        "transmission_total": _round(transmission_total),
        "thermal_bridge_loss": _round(thermal_bridge_loss),
        "ventilation_loss": _round(H_V),
        "envelope_total": _round(envelope_total_wk),
        "H_T": _round(H_T),
        "H_V": _round(H_V),
        "H_tot": _round(H_tot),
        # ----- Gewinne -----
        "solar_gain_kwh": _round(solar_gain_simplified_kwh),
        "solar_gain_monthly_kwh": _round(annual_solar_gains_kwh),  # aus Monatsbilanz
        "internal_gains_kwh": _round(annual_internal_gains_kwh),
        "usable_gains_kwh": _round(usable_gains_kwh),
        # ----- Energiebedarf -----
        "annual_losses_kwh": _round(annual_losses_kwh),
        "annual_heat_demand_kwh": _round(annual_heat_demand_kwh),        # Brutto (Gradstunden)
        "annual_heat_demand_monthly_kwh": _round(annual_heat_demand_monthly_kwh),  # Monatsbilanz
        "adjusted_heat_demand_kwh": _round(adjusted_heat_demand_kwh),   # Netto (brutto - solar)
        "specific_heat_demand": _round(specific_heat_demand),
        "gradstunden": gradstunden,
        # ----- Bewertung -----
        "rating_label": rating["label"],
        "rating_color": rating["color"],
        "rating_message": rating["message"],
        # ----- Dynamische Parameter -----
        "thermal_time_constant_h": _round(tau_h, 1),
        "thermal_mass_class": p["thermal_mass_class"],
        "C_m_total_kwh_per_k": _round(C_m / 1000.0, 1),
        "heat_recovery": _round(p["heat_recovery"], 2),
        "volume_m3": _round(volume),
        "total_envelope_area_m2": _round(total_envelope_area),
        # ----- Klima -----
        "climate_location_key": p["climate_location"],
        "climate_location_label": climate["label"],
        "indoor_setpoint": _round(theta_int, 1),
        "elevation_m": _round(p["elevation_m"], 0),
        "elevation_delta_k": _round(elevation_delta_k, 2),
        # ----- Nutzung / Personen -----
        "building_type": p["building_type"],
        "building_type_variant": p["building_type_variant"],
        "usage_label": p["usage_label"],
        "personendichte": _round(p["personendichte"], 1),
        "n_persons": _round(p.get("n_persons", 0.0), 1),
        "internal_gains_density": _round(p["internal_gains_density"], 2),
        "occupancy_hours": _round(p["occupancy_hours"], 0),
        "air_change_rate": _round(p["air_change_rate"], 2),
        # ----- Monatsbilanz -----
        "monthly_balance": monthly_balance,
        # ----- Zonen -----
        "zone_count": zone_summary["count"],
        "zone_total_area": zone_summary["total_area"],
        "zone_dominant_profile": zone_summary["dominant_profile"],
        "zone_weighted_air_change_rate": zone_summary["weighted_air_change_rate"],
        "zone_weighted_internal_gains_density": zone_summary["weighted_internal_gains_density"],
        "zone_weighted_occupancy_hours": zone_summary["weighted_occupancy_hours"],
        "zone_weighted_gain_utilization_factor": zone_summary["weighted_gain_utilization_factor"],
        "zone_weighted_setpoint_temperature": zone_summary["weighted_setpoint_temperature"],
        "zones": zone_summary["zones"],
        "calculation_basis": (
            "Monatsbilanzverfahren nach DIN EN ISO 13790 / DIN V 18599-2 "
            "mit dynamischem Gewinnnutzungsgrad und standortspezifischen Klimadaten."
        ),
    }


# =============================================================================
# ANLAGENTECHNIK (Endenergie → Primärenergie/CO2, GEG 2024)
# =============================================================================
def calculate_system_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    heat_demand_net = safe_float(data.get("heat_demand_net"))
    bgf = safe_float(data.get("bgf"))
    heating_system = str(data.get("heating_system", "gas")).lower().strip()
    efficiency = safe_float(data.get("efficiency"), DEFAULT_EFFICIENCY)
    cop = safe_float(data.get("cop"), DEFAULT_COP)
    cop_hw = safe_float(data.get("cop_hotwater"), DEFAULT_COP_HOTWATER)

    # Warmwasser: Vorzug Default · BGF (DIN V 18599-10), Fallback Pauschalwert
    hotwater_default = (
        bgf * DEFAULT_HOTWATER_DEMAND_PER_M2 if bgf > 0 else DEFAULT_HOTWATER_DEMAND
    )
    hotwater_demand = safe_float(data.get("hotwater_demand"), hotwater_default)
    auxiliary_electricity = safe_float(data.get("auxiliary_electricity"), DEFAULT_AUXILIARY_ELECTRICITY)

    # PV-Eigenverbrauch zieht Strombezug ab (gilt für Hilfsstrom + WP-Strom)
    pv_self_consumption_kwh = safe_float(data.get("pv_self_consumption_kwh"), 0.0)

    errors: List[str] = []
    validate_non_negative("Heizwärmebedarf netto", heat_demand_net, errors)
    validate_non_negative("BGF", bgf, errors)
    validate_non_negative("Warmwasserbedarf", hotwater_demand, errors)
    validate_non_negative("Hilfsstrom", auxiliary_electricity, errors)
    validate_non_negative("PV Eigenverbrauch", pv_self_consumption_kwh, errors)

    if bgf == 0:
        errors.append("BGF darf nicht 0 sein.")
    if heating_system not in VALID_HEATING_SYSTEMS:
        errors.append(f"Ungültiges Heizsystem '{heating_system}'. Erlaubt: {VALID_HEATING_SYSTEMS}")
    if efficiency <= 0 or efficiency > MAX_EFFICIENCY:
        errors.append(f"Wirkungsgrad muss > 0 und ≤ {MAX_EFFICIENCY} sein.")
    if cop <= 0 or cop > MAX_COP:
        errors.append(f"COP muss > 0 und ≤ {MAX_COP} sein.")

    if errors:
        return {"ok": False, "errors": errors}

    # ===== Endenergiebedarf =====
    if heating_system == "heatpump":
        heating_end_energy = heat_demand_net / cop
        hotwater_end_energy = hotwater_demand / cop_hw
        carrier_for_heating = "heatpump"   # Strom
    else:
        heating_end_energy = heat_demand_net / efficiency
        hotwater_end_energy = hotwater_demand / efficiency
        carrier_for_heating = heating_system

    # Stromverbrauch (Hilfsstrom + ggf. WP) wird durch PV-Eigenverbrauch reduziert
    if heating_system == "heatpump":
        electricity_demand_gross = heating_end_energy + hotwater_end_energy + auxiliary_electricity
    else:
        electricity_demand_gross = auxiliary_electricity

    electricity_from_grid = max(0.0, electricity_demand_gross - pv_self_consumption_kwh)
    electricity_offset_by_pv = electricity_demand_gross - electricity_from_grid

    # Energieträger-Endenergie (ohne PV bereits abgezogen)
    if heating_system == "heatpump":
        fuel_end_energy = 0.0
    else:
        fuel_end_energy = heating_end_energy + hotwater_end_energy

    total_end_energy = fuel_end_energy + electricity_from_grid + electricity_offset_by_pv  # = gross

    # ===== Primärenergie (GEG 2024) =====
    f_p_fuel = PRIMARY_ENERGY_FACTORS.get(carrier_for_heating, 1.1)
    f_p_elec = PRIMARY_ENERGY_FACTORS["electricity"]
    f_p_pv   = PRIMARY_ENERGY_FACTORS["pv_self"]

    f_p_nren_fuel = NREN_PRIMARY_FACTORS.get(carrier_for_heating, 1.1)
    f_p_nren_elec = NREN_PRIMARY_FACTORS["electricity"]

    primary_energy = (
        fuel_end_energy * f_p_fuel
        + electricity_from_grid * f_p_elec
        + electricity_offset_by_pv * f_p_pv
    )
    non_renewable_primary_energy = (
        fuel_end_energy * f_p_nren_fuel
        + electricity_from_grid * f_p_nren_elec
    )

    # ===== CO2-Emissionen (Endenergie · Faktor) =====
    co2_fuel = fuel_end_energy * CO2_FACTORS.get(carrier_for_heating, 0.25)
    co2_grid = electricity_from_grid * CO2_FACTORS["electricity"]
    co2_emissions = co2_fuel + co2_grid

    specific_end_energy = total_end_energy / bgf
    specific_primary_energy = primary_energy / bgf
    specific_nren = non_renewable_primary_energy / bgf
    specific_co2 = co2_emissions / bgf

    # ===== Bewertung Anlagentechnik (nach nicht-erneuerbarem Primärenergie) =====
    benchmark = specific_nren
    if benchmark <= SYSTEM_RATING_THRESHOLDS['efficient']:
        system_label = "Sehr effizient"
        system_color = "green"
        system_message = "Anlagentechnik energetisch günstig (GEG-Niveau erreicht)."
    elif benchmark <= SYSTEM_RATING_THRESHOLDS['medium']:
        system_label = "Mittel"
        system_color = "yellow"
        system_message = "Anlagentechnik nutzbar, aber optimierbar."
    else:
        system_label = "Verbesserungsbedarf"
        system_color = "red"
        system_message = "Hohe nicht-erneuerbare Primärenergie – GEG-Anforderung evtl. nicht erfüllt."

    return {
        "ok": True,
        # ----- Endenergie -----
        "heating_end_energy": _round(heating_end_energy),
        "hotwater_end_energy": _round(hotwater_end_energy),
        "auxiliary_electricity": _round(auxiliary_electricity),
        "fuel_end_energy": _round(fuel_end_energy),
        "electricity_demand_gross": _round(electricity_demand_gross),
        "electricity_from_grid": _round(electricity_from_grid),
        "electricity_offset_by_pv": _round(electricity_offset_by_pv),
        "total_end_energy": _round(total_end_energy),
        "adjusted_heat_demand_net": _round(heat_demand_net),  # Legacy
        # ----- Primärenergie -----
        "primary_energy": _round(primary_energy),
        "non_renewable_primary_energy": _round(non_renewable_primary_energy),
        "specific_end_energy": _round(specific_end_energy),
        "specific_primary_energy": _round(specific_primary_energy),
        "specific_non_renewable_primary_energy": _round(specific_nren),
        # ----- CO2 -----
        "co2_emissions": _round(co2_emissions),
        "co2_from_fuel": _round(co2_fuel),
        "co2_from_grid_electricity": _round(co2_grid),
        "specific_co2": _round(specific_co2, 3),
        # ----- Bewertung -----
        "system_label": system_label,
        "system_color": system_color,
        "system_message": system_message,
        # ----- Faktoren (Nachvollziehbarkeit) -----
        "factors_used": {
            "carrier": carrier_for_heating,
            "primary_factor_fuel": f_p_fuel,
            "primary_factor_electricity": f_p_elec,
            "nren_factor_fuel": f_p_nren_fuel,
            "nren_factor_electricity": f_p_nren_elec,
            "co2_factor_fuel": CO2_FACTORS.get(carrier_for_heating, 0.25),
            "co2_factor_electricity": CO2_FACTORS["electricity"],
        },
        "calculation_basis": (
            "Anlagentechnik nach GEG 2024 §22/Anlage 4 mit nicht-erneuerbarem "
            "Primärenergieanteil und PV-Eigenverbrauchs-Anrechnung."
        ),
    }


# =============================================================================
# GEG-REFERENZGEBÄUDE (vereinfachter Soll-Ist-Vergleich)
# =============================================================================
def calculate_reference_building(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Berechnet das Referenzgebäude nach GEG 2024 Anlage 1 mit den
    Soll-U-Werten und liefert beide Heizwärmebedarfe zum Vergleich.

    Vereinfachung: nutzt dieselbe Geometrie/Klima wie das Ist-Gebäude,
    ersetzt aber alle U-Werte und g-Wert durch GEG-Sollwerte.
    """
    ref_data = dict(data)
    ref_data.update({
        "north_u": GEG_REFERENCE_U_VALUES['wall_outside'],
        "south_u": GEG_REFERENCE_U_VALUES['wall_outside'],
        "east_u":  GEG_REFERENCE_U_VALUES['wall_outside'],
        "west_u":  GEG_REFERENCE_U_VALUES['wall_outside'],
        "roof_u":  GEG_REFERENCE_U_VALUES['roof'],
        "floor_u": GEG_REFERENCE_U_VALUES['floor'],
        "window_u": GEG_REFERENCE_U_VALUES['window'],
        "door_u":  GEG_REFERENCE_U_VALUES['door'],
        "g_value": GEG_REFERENCE_U_VALUES['g_value'],
        "thermal_bridge_factor": GEG_REFERENCE_U_VALUES['thermal_bridge'],
        "air_change_rate": GEG_REFERENCE_U_VALUES['air_change'],
        "heat_recovery": 0.0,
    })
    ref = calculate_envelope_profile(ref_data)
    actual = calculate_envelope_profile(data)

    if not ref.get("ok") or not actual.get("ok"):
        return {"ok": False, "errors": (ref.get("errors") or []) + (actual.get("errors") or [])}

    delta = actual["specific_heat_demand"] - ref["specific_heat_demand"]
    ratio = (actual["specific_heat_demand"] / ref["specific_heat_demand"]) if ref["specific_heat_demand"] > 0 else None
    compliant = ratio is not None and ratio <= 1.0

    return {
        "ok": True,
        "actual_specific_heat_demand": actual["specific_heat_demand"],
        "reference_specific_heat_demand": ref["specific_heat_demand"],
        "delta_specific": _round(delta),
        "ratio_actual_to_reference": _round(ratio, 3) if ratio is not None else None,
        "geg_compliant_envelope": compliant,
        "reference_primary_limit_kwh_m2a": GEG_REFERENCE_PRIMARY_LIMIT,
        "message": (
            "Hülle erfüllt GEG-Referenzniveau." if compliant
            else "Hülle liegt über GEG-Referenz – Nachweis nicht erfüllt."
        ),
    }
