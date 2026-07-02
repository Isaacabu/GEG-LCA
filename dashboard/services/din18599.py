"""
DIN V 18599 – Heizwärmebedarf nach Monatsbilanzverfahren (Stufe 1).

Ersetzt das frühere Gradstundenverfahren. Die hier hinterlegten Werte wurden direkt
aus den Normteilen verifiziert (siehe docs/DIN18599_Umsetzung.md):

- Verfahren / Gleichungen: DIN V 18599-2:2018-09, §5–6
- Nutzungsrandbedingungen:  DIN V 18599-10:2018-09, Tabelle 4 (Wohnen) + Anhang A (NWG)
- Referenzklima Potsdam:     DIN V 18599-10:2018-09, Tabelle E.6
- Primärenergie-/CO₂-Faktoren: DIN V 18599-1:2018-09, Tabelle A.1

Bewusst dokumentierte Vereinfachungen für Stufe 1:
- Ein-Zonen-Modell; bundesweit Referenzklima Deutschland (Potsdam) statt 15 Klimaregionen.
- Konstante Luftwechselrate je Monat (kein detaillierter Teil-6-Anlagenansatz).
- Nachtabsenkung (reduzierter Betrieb, ΔQ_c,b) noch nicht berücksichtigt → leicht konservativ.
- Verschattung pauschal (F_S = 0,9); erdberührte F_x über Profil/Frontend.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..utils import safe_float, validate_non_negative, validate_u_value, get_rating
from ..constants import DEFAULT_G_VALUE, MAX_G_VALUE, MIN_G_VALUE
from .climate import resolve_region

# ---------------------------------------------------------------------------
# Referenzklima Deutschland / Potsdam – DIN V 18599-10, Tabelle E.6
# I_S = mittlere monatliche Strahlungsintensität (24-h-Mittel) in W/m².
# ---------------------------------------------------------------------------
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_NAMES = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
               "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

THETA_E = [1.0, 1.9, 4.7, 9.2, 14.1, 16.7, 19.0, 18.6, 14.3, 9.5, 4.1, 0.9]
STATION_ELEVATION_M = 81.0   # Höhe der Referenzstation Potsdam [m ü. NN]
LAPSE_RATE_K_PER_M = 0.0065  # Höhenkorrektur der Lufttemperatur (Teil 10, Anhang E)

I_S = {
    "horizontal": [29, 44, 97, 189, 221, 241, 210, 180, 127, 77, 31, 17],
    "south":      [59, 47, 98, 147, 132, 124, 113, 127, 123, 106, 39, 29],
    "east":       [25, 29, 68, 134, 137, 150, 138, 115, 83, 55, 20, 12],
    "west":       [17, 24, 60, 114, 127, 136, 117, 105, 79, 47, 19, 11],
    "north":      [10, 18, 31, 58, 75, 83, 81, 57, 41, 25, 13, 7],
}
# Diagonale Orientierungen (NO/SO/SW/NW): Näherung als Mittel der beiden Nachbarn,
# da die Potsdam-Referenztabelle (Teil 10) hier keine Direktwerte liefert.
for _a, _b, _diag in (("north", "east", "northeast"), ("south", "east", "southeast"),
                      ("south", "west", "southwest"), ("north", "west", "northwest")):
    I_S[_diag] = [round((I_S[_a][m] + I_S[_b][m]) / 2.0, 1) for m in range(12)]

# Orientierungen der wärmeübertragenden Hülle (feiner als nur N/S/O/W).
# Reihenfolge im Uhrzeigersinn ab Norden.
ORIENTATIONS = ("north", "northeast", "east", "southeast",
                "south", "southwest", "west", "northwest")

CLIMATE_LABEL = "Referenzklima Deutschland (Potsdam)"

# ---------------------------------------------------------------------------
# Konstanten DIN V 18599-2
# ---------------------------------------------------------------------------
C_AIR = 0.34          # Wärmespeicherfähigkeit Luft, Wh/(m³·K) – §6.3, Gl. (63)
# Abminderungsfaktoren für solare Gewinne durch Fenster (§6.4). Bezeichnungen wie in
# der DIN/Betreuer-Referenz: F_F Rahmen · F_S bauliche Verschattung ·
# F_W nicht senkrechter Strahlungseinfall · F_V Verschmutzung.
F_FRAME = 0.7         # Rahmenanteil F_F (Anteil transparenter Fläche) – §6.4
F_SHADING = 0.9       # bauliche Verschattung F_S (Default ohne Verbauung) – §6.4.3
F_INCIDENCE = 0.9     # nicht senkrechter Strahlungseinfall F_W – §6.4
F_SOILING = 0.9       # Verschmutzung F_V – §6.4
TAU_0 = 16.0          # h, Monatsbilanz – §6.7.3, Gl. (144)
A_0 = 1.0             # –, Monatsbilanz – §6.7.3, Gl. (144)
DELTA_U_WB = 0.10     # W/(m²K) pauschaler Wärmebrückenzuschlag – Gl. (47) / GEG §24
AIR_VOLUME_FACTOR_SMALL = 0.76   # V_Luft = 0,76·V_e (Gebäude ≤ 3 Vollgeschosse, DIN V 18599-1)
AIR_VOLUME_FACTOR_LARGE = 0.80   # V_Luft = 0,80·V_e (sonst)

# Wirksame Wärmekapazität c_wirk [Wh/(m²·K)] – §6.7.1, Gl. (135)–(137)
C_WIRK = {"leicht": 50.0, "mittel": 90.0, "schwer": 130.0}

# ---------------------------------------------------------------------------
# Nutzungsrandbedingungen – DIN V 18599-10
# theta_i: Raum-Solltemperatur Heizfall [°C]
# q_i:     interne Wärmequellen je Nutzungstag [Wh/(m²·d)]  (Personen + Geräte, "mittel")
# usage_days: jährliche Nutzungstage [d/a]
# air_change: Standard-Luftwechselrate [h⁻¹] (effektiv, Monatsansatz)
# ---------------------------------------------------------------------------
# usage_hours: tägliche Nutzungsstunden (Teil 10, Nutzungszeit von–bis). Der Profil-
# Luftwechsel gilt nur während der Nutzung; außerhalb wirkt nur Infiltration.
# heat_op_hours: tägliche Betriebsdauer der Heizung (Teil 10; Wohnen 17 h = 6–23 Uhr).
# na_mode: reduzierter Nachtbetrieb (Teil 10 Tab. 4, Fußn. b): EFH Abschaltung, sonst Absenkung.
PROFILES: Dict[str, Dict[str, Any]] = {
    "wohngebaeude_efh": {"label": "Wohngebäude (EFH)", "theta_i": 20.0, "q_i": 45.0,
                          "usage_days": 365, "usage_hours": 24.0, "air_change": 0.5, "occ_area": 60.0,
                          "heat_op_hours": 17.0, "na_mode": "abschaltung"},
    "wohngebaeude_mfh": {"label": "Wohngebäude (MFH)", "theta_i": 20.0, "q_i": 90.0,
                          "usage_days": 365, "usage_hours": 24.0, "air_change": 0.5, "occ_area": 40.0,
                          "heat_op_hours": 17.0, "na_mode": "absenkung"},
    "einzelbuero":      {"label": "Einzelbüro", "theta_i": 21.0, "q_i": 73.0,
                          "usage_days": 250, "usage_hours": 11.0, "air_change": 0.7, "occ_area": 14.0,
                          "heat_op_hours": 13.0, "na_mode": "absenkung"},
    "gruppenbuero":     {"label": "Gruppenbüro", "theta_i": 21.0, "q_i": 73.0,
                          "usage_days": 250, "usage_hours": 11.0, "air_change": 0.7, "occ_area": 14.0,
                          "heat_op_hours": 13.0, "na_mode": "absenkung"},
    "grossraumbuero":   {"label": "Großraumbüro", "theta_i": 21.0, "q_i": 102.0,
                          "usage_days": 250, "usage_hours": 11.0, "air_change": 0.8, "occ_area": 10.0,
                          "heat_op_hours": 13.0, "na_mode": "absenkung"},
    "besprechung":      {"label": "Besprechung/Sitzung", "theta_i": 21.0, "q_i": 101.0,
                          "usage_days": 250, "usage_hours": 11.0, "air_change": 1.0, "occ_area": 3.0,
                          "heat_op_hours": 13.0, "na_mode": "absenkung"},
    "klassenzimmer":    {"label": "Klassenzimmer (Schule)", "theta_i": 21.0, "q_i": 120.0,
                          "usage_days": 200, "usage_hours": 7.0, "air_change": 0.8, "occ_area": 3.0,
                          "heat_op_hours": 9.0, "na_mode": "absenkung"},
}
N_INFILTRATION = 0.15   # h⁻¹ Grund-Luftwechsel außerhalb der Nutzungszeit (Infiltration)
DELTA_THETA_NA = 4.0    # K zulässige Absenkung der Innentemperatur (Teil 10)
DEFAULT_PROFILE = "wohngebaeude_efh"

# Kühl-Solltemperatur θ_i,c [°C] (Teil 10, Kühlfall) je Profil und ob Kühlung im
# Standardfall angesetzt wird. Wohngebäude: i. d. R. keine aktive Kühlung.
COOLING_SETPOINT = {
    "wohngebaeude_efh": 26.0, "wohngebaeude_mfh": 26.0,
    "einzelbuero": 26.0, "gruppenbuero": 26.0, "grossraumbuero": 26.0,
    "besprechung": 26.0, "klassenzimmer": 26.0,
}
COOLING_DEFAULT_ON = {"wohngebaeude_efh": False, "wohngebaeude_mfh": False}

# Mapping der Frontend-Felder (building_type / building_type_variant) auf Profile.
# Wichtig: Das Frontend sendet die Varianten aus dem Gebäudedaten-Tab wörtlich
# (z. B. "Schulgebäude", "Bürogebäude") – alle müssen hier auflösbar sein, sonst
# fällt die Berechnung still auf das EFH-Profil zurück (Bug, behoben).
_VARIANT_MAP = {
    "efh": "wohngebaeude_efh", "einfamilienhaus": "wohngebaeude_efh",
    "reihenhaus": "wohngebaeude_efh", "doppelhaushälfte": "wohngebaeude_efh",
    "doppelhaushaelfte": "wohngebaeude_efh",
    "mfh": "wohngebaeude_mfh", "mehrfamilienhaus": "wohngebaeude_mfh",
    "einzelbuero": "einzelbuero", "einzelbüro": "einzelbuero", "buero": "einzelbuero",
    "büro": "einzelbuero", "office": "einzelbuero",
    "buerogebaeude": "einzelbuero", "bürogebäude": "einzelbuero",
    "verwaltungsgebaeude": "einzelbuero", "verwaltungsgebäude": "einzelbuero",
    "gruppenbuero": "gruppenbuero", "gruppenbüro": "gruppenbuero",
    "grossraumbuero": "grossraumbuero", "großraumbüro": "grossraumbuero",
    "besprechung": "besprechung", "meeting": "besprechung",
    "klassenzimmer": "klassenzimmer", "schule": "klassenzimmer", "school": "klassenzimmer",
    "schulgebaeude": "klassenzimmer", "schulgebäude": "klassenzimmer",
    "kindergarten": "klassenzimmer",
    # Nutzungen ohne eigenes Teil-10-Profil im Tool → nächstliegendes Profil
    # (dokumentierte Näherung; eigene Profile sind späterer Ausbau).
    "hotel": "wohngebaeude_mfh", "krankenhaus": "wohngebaeude_mfh",
    "einzelhandel": "grossraumbuero", "lagerhalle": "einzelbuero",
    "produktionshalle": "einzelbuero", "gewerbe/werkstatt": "einzelbuero",
    "industriegebaeude": "einzelbuero", "industriegebäude": "einzelbuero",
}


def resolve_profile(building_type: str, variant: str) -> str:
    v = (variant or "").strip().lower()
    if v in _VARIANT_MAP:
        return _VARIANT_MAP[v]
    # Normalisieren: Umlaute/Unterstriche, damit z. B. "nicht_wohngebaeude" greift
    bt = (building_type or "").strip().lower().replace("_", "").replace("-", "")
    if "nichtwohn" in bt or "nwg" in bt:
        return "einzelbuero"
    return DEFAULT_PROFILE


def utilization_factor(gamma: float, tau: float) -> float:
    """Monatlicher Ausnutzungsgrad η der Wärmequellen – DIN V 18599-2, Gl. (24)–(26)."""
    a = A_0 + tau / TAU_0
    if gamma <= 0:
        return 0.0
    if abs(gamma - 1.0) < 1e-9:
        return a / (a + 1.0)
    return (1.0 - gamma ** a) / (1.0 - gamma ** (a + 1.0))


def cooling_utilization_factor(gamma_c: float, tau: float) -> float:
    """Ausnutzungsgrad der Wärmesenken für die Kühlung η_c – DIN V 18599-2 (Kühlfall,
    analog ISO 13790, Gl. 27–29). γ_c = Q_quelle,c / Q_senke,c."""
    a = A_0 + tau / TAU_0
    if gamma_c <= 0:
        return 1.0
    if abs(gamma_c - 1.0) < 1e-9:
        return a / (a + 1.0)
    return (1.0 - gamma_c ** (-a)) / (1.0 - gamma_c ** (-(a + 1.0)))


def calculate_heat_demand(data: Dict[str, Any]) -> Dict[str, Any]:
    """Heizwärmebedarf nach DIN V 18599-2 Monatsbilanzverfahren.

    Erwartet dieselben Eingabefelder, die das Frontend bereits sendet, und liefert
    dieselben Ergebnisfelder zurück, die index.html anzeigt – ergänzt um DIN-Kennwerte.
    """
    bgf = safe_float(data.get("bgf"), 0)
    room_height = safe_float(data.get("room_height"), 3.0) or 3.0
    volume_gross = safe_float(data.get("volume"), 0.0)
    if volume_gross > 0:
        # Geometrie liefert Brutto-Volumen V_e → Luftvolumen nach DIN V 18599-1:
        # V_Luft = 0,76·V_e (≤ 3 Vollgeschosse) bzw. 0,80·V_e.
        n_storeys = safe_float(data.get("n_storeys"), 0)
        if n_storeys <= 0 and room_height > 0:
            n_storeys = max(round(volume_gross / max(bgf * room_height, 1.0)), 1)
        factor = AIR_VOLUME_FACTOR_SMALL if n_storeys <= 3 else AIR_VOLUME_FACTOR_LARGE
        volume = volume_gross * factor
    else:
        # Fallback BGF·Raumhöhe ist bereits näherungsweise das Luftvolumen.
        volume = bgf * room_height

    profile_key = resolve_profile(data.get("building_type", ""), data.get("building_type_variant", ""))
    profile = PROFILES[profile_key]

    # Solltemperatur: Eingabe hat Vorrang, sonst Profilwert.
    theta_i = safe_float(data.get("setpoint_temperature"), 0.0)
    if theta_i <= 0:
        theta_i = profile["theta_i"]

    # Kühlung (Teil 2): Kühl-Solltemperatur + ob aktive Kühlung angesetzt wird.
    theta_i_c = COOLING_SETPOINT.get(profile_key, 26.0)
    ci = safe_float(data.get("cooling_setpoint_temperature"), 0.0)
    if ci > 0:
        theta_i_c = ci
    cooling_enabled = bool(data.get("cooling_enabled",
                                    COOLING_DEFAULT_ON.get(profile_key, True)))

    air_change = safe_float(data.get("air_change_rate"), 0.0)
    if air_change <= 0:
        air_change = safe_float(data.get("ventilation_air_change_rate"), 0.0)
    if air_change <= 0:
        # Profil-Luftwechsel gilt nur während der Nutzungszeit (Teil 10); außerhalb
        # wirkt nur Infiltration → zeitgewichteter effektiver Luftwechsel.
        usage_share = (profile["usage_days"] / 365.0) * (profile["usage_hours"] / 24.0)
        air_change = (profile["air_change"] * usage_share
                      + N_INFILTRATION * (1.0 - usage_share))

    construction_class = str(data.get("construction_class", "mittel")).strip().lower()
    c_wirk_spec = C_WIRK.get(construction_class, C_WIRK["mittel"])

    g_value = safe_float(data.get("g_value"), DEFAULT_G_VALUE)

    # --- Bauteilflächen und (effektive, bereits mit F_x belegte) U-Werte ---
    # Flächen je Orientierung (8 Richtungen). Nicht gesetzte Orientierungen → 0,
    # daher bleiben reine N/S/O/W-Eingaben (einfache Geometrie) unverändert.
    walls = {o: (safe_float(data.get(f"{o}_area")), safe_float(data.get(f"{o}_u")))
             for o in ORIENTATIONS}
    roof_area, roof_u = safe_float(data.get("roof_area")), safe_float(data.get("roof_u"))
    floor_area, floor_u = safe_float(data.get("floor_area")), safe_float(data.get("floor_u"))

    windows = {o: safe_float(data.get(f"window_{o}_area")) for o in ORIENTATIONS}
    window_u = safe_float(data.get("window_u"))

    door_area_per_unit = safe_float(data.get("door_area_per_unit"), 2.0)
    door_u = safe_float(data.get("door_u"))
    door_areas = {o: safe_float(data.get(f"door_{o}_count")) * door_area_per_unit
                  for o in ORIENTATIONS}

    # --- Validierung ---
    errors: List[str] = []
    validate_non_negative("BGF", bgf, errors)
    for name, (area, u) in walls.items():
        validate_non_negative(f"{name} Fläche", area, errors)
        if area > 0:
            validate_u_value(f"{name} U-Wert", u, errors)
    validate_non_negative("Dachfläche", roof_area, errors)
    validate_non_negative("Bodenfläche", floor_area, errors)
    validate_u_value("Dach U-Wert", roof_u, errors)
    validate_u_value("Boden U-Wert", floor_u, errors)
    validate_u_value("Fenster U-Wert", window_u, errors)
    if g_value < MIN_G_VALUE or g_value > MAX_G_VALUE:
        errors.append(f"g-Wert muss zwischen {MIN_G_VALUE} und {MAX_G_VALUE} liegen.")
    if bgf == 0:
        errors.append("BGF darf nicht 0 sein, da sonst kein spezifischer Wert berechnet werden kann.")
    if errors:
        return {"ok": False, "errors": errors}

    # --- Transmissions-Wärmetransferkoeffizienten [W/K] (DIN V 18599-2, Gl. 47) ---
    # Die Geometrie liefert Brutto-Fassadenflächen → Fenster- und Türflächen werden
    # je Orientierung abgezogen (sonst Doppelzählung der Öffnungsflächen).
    # F_x je Orientierung (vom Frontend; Wand an beheizten Raum → 0). Ohne Angabe: 1.
    def _wall_fx(o: str) -> float:
        v = safe_float(data.get(f"{o}_fx"), -1.0)
        return v if 0.0 <= v <= 1.0 else 1.0

    wall_net = {}
    for o, (a, u) in walls.items():
        net = max(a - windows.get(o, 0.0) - door_areas.get(o, 0.0), 0.0)
        wall_net[o] = (net, u)
    wall_losses = {o: round(a * u, 2) for o, (a, u) in wall_net.items()}
    wall_total = sum(wall_losses.values())
    roof_loss = round(roof_area * roof_u, 2)
    floor_loss = round(floor_area * floor_u, 2)
    # Fenster/Türen sitzen in der jeweiligen Wand → gleiche Randbedingung F_x
    window_losses = {o: round(windows[o] * window_u * _wall_fx(o), 2) for o in windows}
    window_total = sum(window_losses.values())
    door_losses = {o: round(door_areas[o] * door_u * _wall_fx(o), 2) for o in door_areas}
    door_total = sum(door_losses.values())

    # Wärmebrückenzuschlag (Gl. 47): H_WB = ΔU_WB · Σ(A_i · F_x,i).
    # F_x = 0 (z. B. Wand an beheizten Nachbarraum) nimmt die Fläche komplett aus der
    # wärmeübertragenden Umfassungsfläche heraus. Ohne F_x-Angabe zählt eine Fläche
    # nur, wenn sie überhaupt Verluste hat (U_eff > 0).
    def _area_fx(key: str, u_eff: float) -> float:
        v = safe_float(data.get(key), -1.0)
        if 0.0 <= v <= 1.0:
            return v
        return 1.0 if u_eff > 0 else 0.0

    wb_area = 0.0
    for o, (a, u) in wall_net.items():
        fx = _area_fx(f"{o}_fx", u)
        wb_area += (a + windows.get(o, 0.0) + door_areas.get(o, 0.0)) * fx
    wb_area += roof_area * _area_fx("roof_fx", roof_u)
    wb_area += floor_area * _area_fx("floor_fx", floor_u)
    envelope_area = wb_area
    # Wärmebrückenzuschlag ΔU_WB (GEG §24 / DIN V 18599-2 Gl. 47): 0,10 pauschal ohne
    # Nachweis · 0,05 mit Gleichwertigkeitsnachweis (DIN 4108 Beiblatt 2) · 0,03
    # wärmebrückenoptimiert (Passivhaus). Eingabe hat Vorrang, sonst Default 0,10.
    delta_u_wb = safe_float(data.get("delta_u_wb"), DELTA_U_WB)
    if not (0.0 <= delta_u_wb <= 0.15):
        delta_u_wb = DELTA_U_WB
    h_bridges = delta_u_wb * wb_area

    # Fenster-Einbauwärmebrücken (linear): H_WB,Fenster = Σ ψ_i · L_i über die
    # Anschlüsse Seiten (Laibung Seite 1+2), Sturz und Brüstung. ψ [W/mK] und die
    # Bezugslängen L [m] (automatisch aus der Fenstergeometrie) kommen vom Frontend.
    def _psi(key: str) -> float:
        v = safe_float(data.get(key), 0.0)
        return v if 0.0 <= v <= 0.5 else 0.0

    def _len(key: str) -> float:
        v = safe_float(data.get(key), 0.0)
        return v if v >= 0.0 else 0.0

    h_window_bridges = (
        _psi("window_psi_seiten") * _len("window_len_seiten")
        + _psi("window_psi_sturz") * _len("window_len_sturz")
        + _psi("window_psi_bruestung") * _len("window_len_bruestung")
    )

    h_t = wall_total + roof_loss + floor_loss + window_total + door_total + h_bridges + h_window_bridges  # [W/K]
    h_v = air_change * volume * C_AIR                                                  # [W/K] (Gl. 63)
    h_total = h_t + h_v

    # --- Wirksame Wärmekapazität & Zeitkonstante (Gl. 135–137, 22) ---
    c_wirk = c_wirk_spec * bgf                       # [Wh/K]
    tau = c_wirk / h_total if h_total > 0 else 0.0   # [h]

    # --- Monatsbilanz (Gl. 1, 24–26) ---
    months = []
    q_h_year = 0.0
    q_c_year = 0.0
    q_sink_year = 0.0
    q_solar_year = 0.0
    q_internal_year = 0.0

    usage_fraction = profile["usage_days"] / 365.0

    # Höhenkorrektur: Standort über der Referenzstation → Außentemperatur sinkt
    elevation_m = safe_float(data.get("elevation_m"), 0.0)
    elevation_delta = (max(elevation_m - STATION_ELEVATION_M, 0.0) * LAPSE_RATE_K_PER_M
                       if elevation_m > 0 else 0.0)

    # Klimaregion aus dem Standort (Bundesland): regionaler Strahlungsfaktor wirkt
    # auf die solaren Gewinne, der Temperatur-Offset auf die Außentemperatur.
    region = resolve_region(data.get("project_state"))
    radiation_factor = float(region["radiation_factor"])
    temp_offset = float(region["temp_offset_k"])

    # Reduzierter Nachtbetrieb (Teil 2, Gl. 28–30): Korrekturfaktor f_NA aus
    # Auskühlzeitkonstante τ; EFH = Heizungsabschaltung (0,26), sonst Absenkung (0,13).
    import math as _math
    night_setback = data.get("night_setback", True)
    t_na = max(24.0 - profile["heat_op_hours"], 0.0)
    f_na = 0.0
    if night_setback and t_na > 0:
        base = 0.26 if profile["na_mode"] == "abschaltung" else 0.13
        f_na = base * _math.exp(-tau / 250.0)

    for m in range(12):
        days = MONTH_DAYS[m]
        hours = days * 24.0
        theta_e = THETA_E[m] - elevation_delta + temp_offset

        # Bilanz-Innentemperatur mit Nachtabsenkung (Gl. 28), gekappt bei Δθ_i,NA
        theta_i_m = theta_i
        if f_na > 0 and theta_i > theta_e:
            theta_i_m = max(theta_i - f_na * (t_na / 24.0) * (theta_i - theta_e),
                            theta_i - DELTA_THETA_NA)
        dt = theta_i_m - theta_e

        # Wärmesenken: Transmission + Lüftung (nur wenn innen wärmer) [kWh]
        q_sink = h_total * dt * hours / 1000.0 if dt > 0 else 0.0

        # Solare Wärmequellen je Orientierung [kWh] (Gl. 112/113)
        # A_eff = A · F_F · F_S · F_W · F_V ; Q_sol = A_eff · g · I_S
        q_solar = 0.0
        for orient in ORIENTATIONS:
            # I_S der Potsdam-Referenz, regional skaliert (Globalstrahlungsniveau)
            irr_kwh = I_S[orient][m] * radiation_factor * 24.0 * days / 1000.0   # kWh/m² im Monat
            q_solar += (windows[orient] * g_value
                        * F_FRAME * F_SHADING * F_INCIDENCE * F_SOILING * irr_kwh)

        # Interne Wärmequellen [kWh] (Teil 10): q_i je Nutzungstag
        usage_days_m = days * usage_fraction
        q_internal = profile["q_i"] * bgf * usage_days_m / 1000.0

        q_source = q_solar + q_internal

        if q_sink > 0:
            gamma = q_source / q_sink
            eta = utilization_factor(gamma, tau)
            q_h = max(q_sink - eta * q_source, 0.0)
        else:
            gamma = 0.0
            eta = 0.0
            q_h = 0.0

        # --- Kühlbedarf Q_c,b (Teil 2, Kühlfall) [kWh] ---
        # Wärmesenke für Kühlung Q_ht,c = H·(θ_i,c − θ_e)·t (negativ bei θ_e > θ_i,c, dann
        # Wärmeeintrag von außen). Q_c = Q_quelle − η_c·Q_senke.
        q_c = 0.0
        if cooling_enabled:
            q_ht_c = h_total * (theta_i_c - theta_e) * hours / 1000.0
            if q_source > 0:
                if q_ht_c <= 0:
                    q_c = q_source - q_ht_c          # Gewinne + Wärmeeintrag von außen
                else:
                    gamma_c = q_source / q_ht_c
                    eta_c = cooling_utilization_factor(gamma_c, tau)
                    q_c = max(q_source - eta_c * q_ht_c, 0.0)

        q_h_year += q_h
        q_c_year += q_c
        q_sink_year += q_sink
        q_solar_year += q_solar
        q_internal_year += q_internal

        months.append({
            "month": MONTH_NAMES[m],
            "theta_e": theta_e,
            "q_sink": round(q_sink, 1),
            "q_solar": round(q_solar, 1),
            "q_internal": round(q_internal, 1),
            "gamma": round(gamma, 3),
            "eta": round(eta, 3),
            "q_heat": round(q_h, 1),
            "q_cool": round(q_c, 1),
        })

    specific = q_h_year / bgf if bgf > 0 else 0.0
    specific_cooling = q_c_year / bgf if bgf > 0 else 0.0
    rating = get_rating(specific)

    # interne Gewinnleistung als Mittel über das Jahr [W/m²] (für Frontend-Anzeige)
    internal_gains_density = profile["q_i"] * usage_fraction / 24.0
    n_persons = bgf / profile["occ_area"] if profile.get("occ_area") else None

    # --- Aufschlüsselung der Wärmebilanz (kWh/a) für die Diagramm-Visualisierung ---
    # Q_h = (H_T + H_V)·(θ_i − θ_e) − η·(Q_S + Q_i). Jede H-Komponente sieht in jedem
    # Monat dieselbe Temperaturdifferenz und Zeit → ihr Anteil an den Brutto-Wärmesenken
    # Q_Senke ist exakt ihr Anteil an H_gesamt. So summieren die Posten genau auf Q_Senke.
    def _sink_share(h_component: float) -> float:
        return (h_component / h_total * q_sink_year) if h_total > 0 else 0.0

    usable_gains = max(q_sink_year - q_h_year, 0.0)   # η·(Q_S + Q_i), tatsächlich genutzt
    heat_balance = {
        # Verluste – Wärmesenken Q_Senke (Transmission je Bauteil + Lüftung)
        "transmission": {
            "walls": round(_sink_share(wall_total), 1),
            "roof": round(_sink_share(roof_loss), 1),
            "floor": round(_sink_share(floor_loss), 1),
            "windows": round(_sink_share(window_total), 1),
            "doors": round(_sink_share(door_total), 1),
            "thermal_bridges": round(_sink_share(h_bridges), 1),
        },
        "transmission_total_kwh": round(_sink_share(h_t), 1),
        "ventilation_kwh": round(_sink_share(h_v), 1),
        "sinks_total_kwh": round(q_sink_year, 1),
        # Gewinne – Wärmequellen Q_Quelle
        "gains": {
            "solar": round(q_solar_year, 1),
            "internal": round(q_internal_year, 1),
        },
        "gains_total_kwh": round(q_solar_year + q_internal_year, 1),
        "usable_gains_kwh": round(usable_gains, 1),
        # Ergebnis Stufe 1
        "heat_demand_kwh": round(q_h_year, 1),
    }

    return {
        "ok": True,
        # --- Bauteil-/Hüllkennwerte (W/K) – unverändertes Anzeigeformat ---
        "north_loss": wall_losses["north"],
        "south_loss": wall_losses["south"],
        "east_loss": wall_losses["east"],
        "west_loss": wall_losses["west"],
        "wall_total": round(wall_total, 2),
        "roof_loss": roof_loss,
        "floor_loss": floor_loss,
        "window_north_loss": window_losses["north"],
        "window_south_loss": window_losses["south"],
        "window_east_loss": window_losses["east"],
        "window_west_loss": window_losses["west"],
        "window_total": round(window_total, 2),
        "door_north_loss": door_losses["north"],
        "door_south_loss": door_losses["south"],
        "door_east_loss": door_losses["east"],
        "door_west_loss": door_losses["west"],
        "door_total": round(door_total, 2),
        # H_T (Transmission) wie bisher als "envelope_total" (W/K); zusätzlich H gesamt.
        "envelope_total": round(h_t, 2),
        "thermal_bridge_loss": round(h_bridges, 2),     # ΔU_WB·A_Hülle [W/K]
        "window_bridge_loss": round(h_window_bridges, 2),  # Σ ψ·L Fenster (Seiten/Sturz/Brüstung) [W/K]
        "delta_u_wb": delta_u_wb,                        # angesetzter Wärmebrückenzuschlag [W/m²K]
        "envelope_area_m2": round(envelope_area, 1),
        "h_transmission": round(h_t, 2),
        "h_ventilation": round(h_v, 2),
        "h_total": round(h_total, 2),
        "time_constant_h": round(tau, 1),
        # --- Energiebilanz (kWh/a) ---
        "annual_heat_demand_kwh": round(q_sink_year, 1),        # Brutto-Wärmesenken
        "solar_gain_kwh": round(q_solar_year, 1),
        "internal_gain_kwh": round(q_internal_year, 1),
        "adjusted_heat_demand_kwh": round(q_h_year, 1),         # Heizwärmebedarf netto Q_h,b,a
        "specific_heat_demand": round(specific, 2),
        # Aufschlüsselung Wärmesenken/-quellen (kWh/a) für die Bilanz-Visualisierung
        "heat_balance": heat_balance,
        # --- Kühlung (Teil 2, Nutzkältebedarf Q_c,b) ---
        "cooling_demand_kwh": round(q_c_year, 1),
        "specific_cooling_demand": round(specific_cooling, 2),
        "cooling_setpoint": theta_i_c if cooling_enabled else None,
        "cooling_enabled": cooling_enabled,
        # --- Bewertung ---
        "rating_label": rating["label"],
        "rating_color": rating["color"],
        "rating_message": rating["message"],
        # --- DIN-Kontext für Frontend-Anzeige ---
        "usage_label": profile["label"],
        "building_type_variant": data.get("building_type_variant", ""),
        "internal_gains_density": round(internal_gains_density, 2),
        "n_persons": round(n_persons, 1) if n_persons is not None else None,
        "climate_location_label": region["label"],
        "climate_region_key": region["key"],
        "climate_radiation_factor": round(radiation_factor, 2),
        "climate_temp_offset_k": round(temp_offset, 1),
        "elevation_m": round(elevation_m, 0),
        "elevation_delta_k": round(elevation_delta, 1),
        "setpoint_temperature": theta_i,
        "air_change_rate": round(air_change, 2),
        "night_setback": ("Heizungsabschaltung nachts" if profile["na_mode"] == "abschaltung"
                          else "Nachtabsenkung") if f_na > 0 else "ohne reduzierten Nachtbetrieb",
        "calculation_basis": "DIN V 18599-2:2018-09, Monatsbilanzverfahren",
        "monthly": months,
    }
