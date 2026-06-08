"""
DIN V 18599 – Anlagentechnik (Stufe 2): Heizung (Teil 5), Trinkwarmwasser (Teil 8),
Wohnungslüftung (Teil 6).

Prozesskette je Monat:
    Nutzenergie → Übergabe → Verteilung → Speicherung → Erzeugung → End-/Primärenergie + CO₂.

Alle Kennwerte sind Norm-Standardwerte; Quellen und Gleichungsnummern siehe
docs/DIN18599_Umsetzung.md, Abschnitte 7–9 (dort gegen die Norm-PDFs verifiziert).

Dokumentierte Vereinfachungen:
- Rückgewinnbare Verluste (Leitungen/Speicher/Erzeuger im beheizten Bereich) werden
  monatlich mit (1 − η_Monat) als Netto-Mehrbedarf angesetzt statt iterativ in Teil 2
  rückgekoppelt (Erstordnungs-Näherung der ungeregelten Wärmeeinträge).
- Elektro-Wärmepumpe: Carnot-Gütegrad-Monatsmodell statt BIN-Verfahren (Anhang B/C),
  Gütegrad aus COP-Eingabe am Prüfpunkt A2/W35; TWW-Senke 55 °C.
- Keine Solarthermie, kein KWK, keine Mehrkesselanlagen (kein UI-Input).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from ..utils import safe_float
from .din18599 import (
    MONTH_DAYS, MONTH_NAMES, THETA_E, PROFILES, N_INFILTRATION,
    resolve_profile, calculate_heat_demand,
)
from .din18599_licht import calculate_lighting

# ---------------------------------------------------------------------------
# Allgemeine Randbedingungen (Teil 8 Tab. 6 / Teil 5 Tab. 24)
# ---------------------------------------------------------------------------
THETA_I_HEATED = 20.0       # °C Umgebung beheizter Bereich
THETA_I_UNHEATED = 13.0     # °C Umgebung unbeheizter Bereich (Keller)
THETA_W_CIRC = 57.5         # °C mittlere TWW-Netztemperatur mit Zirkulation
THETA_S_AV = 55.0           # °C mittlere Speichertemperatur
THETA_COLD = 10.0           # °C Kaltwasser
THETA_E_DESIGN = -14.0      # °C Norm-Außentemperatur Potsdam (Heizlast-Auslegung)

U_PIPE_V = 0.200            # W/(m·K) Verteilung, gedämmt nach 1995 (Tab. 8/27)
U_PIPE_SA = 0.255           # W/(m·K) Strang/Anbindung, gedämmt nach 1995

F_HS_HI = {"gas": 1.11, "pellet": 1.08}   # Brennwert/Heizwert-Verhältnis (Teil 5, 4.2)

# Primärenergie- (GEG 2024 Anlage 4) und CO₂-Faktoren (GEG Anlage 9), je Energieträger.
F_PRIMARY = {"gas": 1.1, "pellet": 0.2, "district": 0.7, "electricity": 1.8}
F_CO2 = {"gas": 0.240, "pellet": 0.020, "district": 0.180, "electricity": 0.560}

# ---------------------------------------------------------------------------
# Heizkessel-Standardwerte (Teil 5 Tab. 49/50, Teil 8 Tab. 30/31) – Neubau ("nach 1994+")
#   eta_Pn/Pint:  (A + B·log10 Pn)/100 bzw. (C + D·log10 Pn)/100   (Gl. 217/218)
#   q_P0,70:      E·Pn^F/100                                        (Gl. 219)
#   K/L:          Temperaturkorrektur (Tab. 39)
# ---------------------------------------------------------------------------
BOILERS = {
    # Gas-Brennwertkessel, "verbessert" (ab 1999) – Standard für Neubau
    "gas": {"A": 94.0, "B": 1.0, "C": 103.0, "D": 1.0, "E": 4.0, "F": -0.4,
            "K": 0.002, "L": 0.002, "condensing": True, "theta_test_pint": 30.0},
    # Pelletkessel, System mit Pufferspeicher (nach 1994)
    "pellet": {"A": 92.0, "B": 0.5, "C": 91.0, "D": 0.8, "E": 3.0, "F": -0.2,
               "K": 0.0, "L": 0.0004, "condensing": False, "theta_test_pint": 70.0},
}
BETA_PINT = 0.3             # Teillast-Prüfpunkt (VO (EU) 813/2013)

# Hilfsenergie Kessel (Gl. 220, Tab. 51, Gebläsebrenner): P_aux = (G + H·Pn^n)/1000 kW
AUX_BOILER_PN = (0.0, 45.0, 0.48)
AUX_BOILER_P0 = (15.0, 0.0, 0.0)

# Fernwärme-Hausstation (Teil 5 Tab. 61/62 = Teil 8 Tab. 34/35; Warmwasser niedrige Temp.)
DISTRICT = {"theta_prim": 105.0, "d_ds": 0.6, "b_ds": 4.0}

# Wärmeübergabe (Teil 5 Tab. 10/11): Δθ_ce-Summanden Standardfall
EMISSION = {
    # Heizkörper: P-Regler 1 K (1,2) + Übertemperatur 30 K / 55/45 (0,5) + Außenwand (0,3)
    "radiator": {"delta_theta_ce": 2.0, "theta_design_vl": 55.0, "theta_design_rl": 45.0,
                 "n_exp": 1.3, "label": "Heizkörper 55/45, Thermostat 1 K"},
    "radiator_70_55": {"delta_theta_ce": 2.2, "theta_design_vl": 70.0, "theta_design_rl": 55.0,
                       "n_exp": 1.3, "label": "Heizkörper 70/55, Thermostat 1 K"},
    # FBH Nasssystem: Regler (1,2) + Δθ_emb (0,35) + angrenzende Flächen Mindestdämmung (0,5)
    "floor": {"delta_theta_ce": 2.05, "theta_design_vl": 35.0, "theta_design_rl": 28.0,
              "n_exp": 1.1, "label": "Fußbodenheizung 35/28"},
}

# Lüftungssysteme (Teil 6): effektiver Bilanz-Luftwechsel + SPI [W/(m³/h)] (Tab. 19)
N_INF = 0.1                 # h⁻¹ Infiltration bei vorhandener Anlage
N_MECH = 0.4                # h⁻¹ Anlagenluftwechsel (nicht bedarfsgeführt)
VENT_SYSTEMS = {
    "none":            {"label": "ohne Lüftungsanlage", "spi_ac": 0.0,  "spi_dc": 0.0,  "hr": False},
    "exhaust":         {"label": "zentrale Abluftanlage", "spi_ac": 0.20, "spi_dc": 0.10, "hr": False},
    "balanced":        {"label": "Zu-/Abluft ohne WRG", "spi_ac": 0.55, "spi_dc": 0.35, "hr": False},
    "balanced_hr":     {"label": "Zu-/Abluft mit WRG", "spi_ac": 0.55, "spi_dc": 0.35, "hr": True},
    "balanced_hr_dec": {"label": "dezentrale Zu-/Abluft mit WRG", "spi_ac": 0.35, "spi_dc": 0.20, "hr": True},
    "exhaust_hp":      {"label": "Abluft/Zuluft-WP ohne WÜ", "spi_ac": 0.65, "spi_dc": 0.45, "hr": False,
                        "n_eff_fixed": 0.7},
    "exhaust_hp_he":   {"label": "Abluft/Zuluft-WP mit WÜ", "spi_ac": 0.65, "spi_dc": 0.45, "hr": False,
                        "n_eff_fixed": 0.6},
}

CARNOT_TEST = (308.15) / (35.0 - 2.0)   # COP_Carnot am Prüfpunkt A2/W35 = 9,338
COP_CAP = 7.0


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def _boiler_eta_pn(b: Dict, p_n: float) -> float:
    return (b["A"] + b["B"] * math.log10(max(p_n, 1.0))) / 100.0


def _boiler_eta_pint(b: Dict, p_n: float) -> float:
    return (b["C"] + b["D"] * math.log10(max(p_n, 1.0))) / 100.0


def _boiler_q_p0_70(b: Dict, p_n: float) -> float:
    return (b["E"] * max(p_n, 1.0) ** b["F"]) / 100.0


def _storage_loss_day(v_s: float) -> float:
    """Bereitschafts-Wärmeverlust Q_s,P0,day [kWh/d] – Teil 8 Gl. (26)/(27)."""
    if v_s <= 0:
        return 0.0
    if v_s <= 1000:
        return 0.8 + 0.02 * v_s ** 0.77
    return 0.39 * v_s ** 0.35 + 0.5


def _pipe_lengths_heating(a_ngf: float, n_g: float, h_g: float, group: int) -> Dict[str, float]:
    """Standard-Leitungslängen Heizung, Netztyp I (Teil 5 Tab. 26)."""
    if group == 2:   # Schulen u. ä.
        l_v = 30.0 + 1.5 * a_ngf ** 0.79
        l_s = 0.0050 * a_ngf + 1.50 * (h_g * n_g) ** 1.0
        l_a = 0.05 * a_ngf
    else:            # Gruppe 1: Wohnen, Büro, Hotels …
        l_v = 30.0 + 2.3 * a_ngf ** 0.79
        l_s = 2.56 * a_ngf ** 0.1 + 0.0006 * a_ngf * h_g * n_g
        l_a = 0.06 * a_ngf ** 1.13
    return {"v": l_v, "s": l_s, "a": l_a}


def _pipe_lengths_dhw(a_ngf: float, n_g: float, group: int) -> Dict[str, float]:
    """Standard-Leitungslängen TWW, Netztyp I Einzonen-Gebäude (Teil 8 Tab. 10)."""
    if group == 2:   # Büro u. ä.
        return {"v": 5.40 * (a_ngf / n_g) ** 0.49, "s": 0.025 * a_ngf ** 0.97,
                "a": 0.02 * a_ngf}
    if group == 3:   # Schulen u. ä.
        return {"v": 5.40 * (a_ngf / n_g) ** 0.49, "s": 0.025 * a_ngf ** 0.97,
                "a": 2.39 * a_ngf ** 0.43}
    # Gruppe 1: Wohnen
    return {"v": 0.11 * (a_ngf / n_g) ** 1.24, "s": 0.005 * a_ngf ** 1.38,
            "a": 0.09 * a_ngf ** 1.00}


def _theta_hk_av(beta: float, em: Dict) -> float:
    """Mittlere Heizkreistemperatur θ_HK,av(β) – Teil 5 Gl. (12)–(16)."""
    beta = min(max(beta, 0.0), 1.0)
    theta_i = 20.0
    theta_m_design = 0.5 * (em["theta_design_vl"] + em["theta_design_rl"])
    return theta_i + (theta_m_design - theta_i) * beta ** (1.0 / em["n_exp"])


def _theta_rl_av(beta: float, em: Dict) -> float:
    beta = min(max(beta, 0.0), 1.0)
    return 20.0 + (em["theta_design_rl"] - 20.0) * beta ** (1.0 / em["n_exp"])


def _monthly_fallback(annual_kwh: float, theta_i: float) -> List[Dict[str, Any]]:
    """Monatsaufteilung über Gradtage, falls keine Hüllendaten mitgesendet werden."""
    weights = []
    for m in range(12):
        dt = theta_i - THETA_E[m]
        # Heizmonate: Außentemperatur unter Heizgrenze 15 °C
        weights.append(dt * MONTH_DAYS[m] if THETA_E[m] < 15.0 and dt > 0 else 0.0)
    total = sum(weights) or 1.0
    months = []
    for m in range(12):
        months.append({"month": MONTH_NAMES[m], "theta_e": THETA_E[m],
                       "q_heat": annual_kwh * weights[m] / total,
                       "eta": 0.98 if weights[m] > 0 else 0.0})
    return months


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------
def calculate_system_din(data: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []

    heating_system = str(data.get("heating_system", "gas")).strip().lower()
    if heating_system not in ("gas", "heatpump", "district", "pellet"):
        return {"ok": False, "errors": ["Ungültiges Heizsystem."]}

    bgf = safe_float(data.get("bgf"), 0)
    if bgf <= 0:
        return {"ok": False, "errors": ["BGF darf nicht 0 sein."]}

    profile_key = resolve_profile(data.get("building_type", ""),
                                  data.get("building_type_variant", ""))
    profile = PROFILES[profile_key]
    is_residential = profile_key.startswith("wohngebaeude")
    is_mfh = profile_key == "wohngebaeude_mfh"

    room_height = safe_float(data.get("room_height"), 3.0) or 3.0
    n_storeys = safe_float(data.get("n_storeys"), 0)
    if n_storeys <= 0:
        n_storeys = 4.0 if is_mfh else (2.0 if is_residential else 3.0)
    volume = safe_float(data.get("volume"), 0.0) or bgf * room_height
    a_floor = bgf / n_storeys
    l_char = b_char = math.sqrt(max(a_floor, 1.0))   # Näherung quadratischer Grundriss

    # --- Lüftungssystem (Teil 6) -------------------------------------------------
    vent_key = str(data.get("ventilation_system_type", "none")).strip().lower()
    vent = VENT_SYSTEMS.get(vent_key, VENT_SYSTEMS["none"])
    hr_eff = safe_float(data.get("ventilation_heat_recovery_eff"), 0.8)
    fan_dc = str(data.get("ventilation_fan_type", "ac")).strip().lower() == "dc"

    if "n_eff_fixed" in vent:
        n_eff = vent["n_eff_fixed"]
    elif vent["hr"]:
        n_eff = N_INF + N_MECH * (1.0 - hr_eff)      # Teil 6 Gl. (14)/(15)
    elif vent_key == "none":
        # Freie Lüftung: Profil-Luftwechsel nutzungszeitgewichtet (wie im Teil-2-Kern)
        usage_share = (profile["usage_days"] / 365.0) * (profile["usage_hours"] / 24.0)
        n_eff = (profile["air_change"] * usage_share
                 + N_INFILTRATION * (1.0 - usage_share))
    else:
        n_eff = N_INF + N_MECH                        # Abluft/Zu-Abluft ohne WRG

    # Aufteilung Lüftung: nur die Infiltration bleibt in der Zonenbilanz (Teil 2);
    # der maschinell geförderte Anteil wird als RLT-Luftaufbereitung (Teil 3) separat
    # auf Raumtemperatur erwärmt (kein doppelter Lüftungs-Wärmeverlust).
    mechanical_vent = vent_key != "none"
    if mechanical_vent:
        n_zone = N_INF
        n_rlt = max(n_eff - N_INF, 0.0)
    else:
        n_zone = n_eff
        n_rlt = 0.0

    # --- Teil-2-Bilanz (mit Lüftungskopplung) ------------------------------------
    envelope = data.get("envelope")
    theta_i = profile["theta_i"]
    cooling_demand_year = 0.0
    cooling_setpoint = None
    if isinstance(envelope, dict) and envelope:
        env = dict(envelope)
        env["air_change_rate"] = n_zone
        base = calculate_heat_demand(env)
        if not base.get("ok"):
            return {"ok": False, "errors": ["Hüllenberechnung fehlgeschlagen: "]
                    + base.get("errors", [])}
        theta_i = base.get("setpoint_temperature", theta_i)
        monthly = base["monthly"]
        q_hb_year = base["adjusted_heat_demand_kwh"]
        h_total = base["h_total"]
        cooling_demand_year = base.get("cooling_demand_kwh", 0.0)
        cooling_setpoint = base.get("cooling_setpoint")
        phi_max = h_total * (theta_i - THETA_E_DESIGN) / 1000.0     # kW Gebäudeheizlast
        basis = "Teil 2 Monatsbilanz (mit Lüftungsanlage neu bilanziert)"
    else:
        q_hb_year = safe_float(data.get("heat_demand_net"), 0.0)
        if q_hb_year < 0:
            errors.append("Heizwärmebedarf darf nicht negativ sein.")
        monthly = _monthly_fallback(q_hb_year, theta_i)
        phi_max = q_hb_year / 1800.0 if q_hb_year > 0 else 5.0      # Vollbenutzungsstunden
        basis = "Monatsaufteilung über Gradtage (Hüllendaten nicht mitgesendet)"
    if errors:
        return {"ok": False, "errors": errors}

    # --- Wärmeübergabe (Teil 5, 6.2) ----------------------------------------------
    emission_key = str(data.get("heat_emission", "")).strip().lower()
    if emission_key not in EMISSION:
        emission_key = "floor" if heating_system == "heatpump" else "radiator"
    em = EMISSION[emission_key]
    f_hydr = 1.02   # hydraulischer Abgleich nach Herstellervorgaben (Tab. 6)

    # --- Heizungs-Verteilnetz (Teil 5, 6.3) ----------------------------------------
    group_h = 2 if profile_key == "klassenzimmer" else 1
    lh = _pipe_lengths_heating(bgf, n_storeys, room_height, group_h)
    pipes_inside = bool(data.get("heating_distribution_inside", False))
    # Erzeuger-Nennleistung
    p_n = safe_float(data.get("nominal_power_kw"), 0.0)
    if p_n <= 0:
        p_n = max(1.2 * phi_max, 11.0 if heating_system in ("gas", "pellet") else phi_max)

    # --- TWW-Nutzenergie (Teil 10) --------------------------------------------------
    if is_residential:
        # A_NGF,WE = NGF je Wohneinheit (Teil 10 Tab. 4); MFH: mittlere WE ≈ 70 m²
        a_we = bgf if not is_mfh else bgf / max(round(bgf / 70.0), 1)
        q_wb_spec = max(16.5 - a_we * 0.05, 8.5)
        q_wb_year = q_wb_spec * bgf                              # kWh/a
    else:
        q_w_d = {"einzelbuero": 30.0, "gruppenbuero": 30.0, "grossraumbuero": 30.0,
                 "besprechung": 30.0, "klassenzimmer": 130.0}.get(profile_key, 30.0)
        q_wb_year = q_w_d * bgf * profile["usage_days"] / 1000.0  # kWh/a
    f_zapf = 0.98       # Thermostatarmaturen (Teil 8 Gl. 12)
    q_wb_year *= f_zapf

    with_circ = data.get("dhw_circulation")
    if with_circ is None:
        with_circ = is_mfh or (not is_residential and bgf > 500)
    with_circ = bool(with_circ)

    group_w = {"klassenzimmer": 3}.get(profile_key, 1 if is_residential else 2)
    lw = _pipe_lengths_dhw(bgf, n_storeys, group_w)
    if not with_circ:
        lw = {"v": lw["v"] / 2.0, "s": lw["s"] / 2.0, "a": lw["a"]}   # 6.2.2.3

    # Speicher (Standard: indirekt beheizt; WP größer dimensioniert)
    v_storage = safe_float(data.get("dhw_storage_liters"), 0.0)
    if v_storage <= 0:
        daily_l = (q_wb_year / 365.0) * 1000.0 / (1.163 * (THETA_S_AV - THETA_COLD))
        v_storage = max(200.0 if heating_system == "heatpump" else 80.0, 2.0 * daily_l)
    q_s_p0_day = _storage_loss_day(v_storage)
    storage_inside = True    # Aufstellung innerhalb der Hülle (Standard)

    # Kessel-Kennwerte
    boiler = BOILERS.get(heating_system)
    f_hs_hi = F_HS_HI.get(heating_system, 1.0)
    if boiler:
        eta_k_pn = _boiler_eta_pn(boiler, p_n)
        eta_k_pint = _boiler_eta_pint(boiler, p_n)
        q_p0_70 = _boiler_q_p0_70(boiler, p_n)
    # Pellet-Pufferspeicher (30 l/kW)
    v_buffer = 30.0 * p_n if heating_system == "pellet" else 0.0
    q_buf_p0_day = _storage_loss_day(v_buffer)

    # Wärmepumpe: Gütegrad aus COP-Eingabe (Prüfpunkt A2/W35)
    cop_input = safe_float(data.get("cop"), 3.5)
    if heating_system == "heatpump" and not (1.5 <= cop_input <= 8.0):
        return {"ok": False, "errors": ["COP muss zwischen 1,5 und 8,0 liegen (Prüfpunkt A2/W35)."]}
    eta_g = cop_input / CARNOT_TEST

    # Fernwärme: mittlere Stationstemperatur (Gl. 244)
    theta_sek = 0.5 * (em["theta_design_vl"] + em["theta_design_rl"])
    theta_ds = DISTRICT["d_ds"] * DISTRICT["theta_prim"] + (1 - DISTRICT["d_ds"]) * theta_sek
    h_ds = DISTRICT["b_ds"] * max(p_n, 1.0) ** (1.0 / 3.0)          # Gl. (243)

    # Zirkulationspumpe (Teil 8, 6.2.2.4)
    w_circ_pump_year = 0.0
    if with_circ:
        z = min(10.0 + 1.0 / (0.07 + 50.0 / bgf), 24.0)             # Gl. (18)
        if is_mfh:
            z = max(z, 16.0)
        p_wda = (U_PIPE_V * lw["v"] + U_PIPE_SA * lw["s"]) * (THETA_W_CIRC - theta_i)  # Gl. (21) [W]
        v_flow = p_wda / (1.15 * 5.0 * 1000.0)                      # Gl. (20) [m³/h]
        l_max_w = 2.0 * (l_char + 2.5 + n_storeys * room_height)    # Gl. (23)
        dp = 0.1 * l_max_w + 12.0 + 1.0                             # Gl. (22) [kPa]
        p_hydr_w = max(0.2778 * dp * v_flow, 1.0)                   # Gl. (19) [W]
        f_e = 1.25 + math.sqrt(200.0 / p_hydr_w)                    # Gl. (24)
        e_aux = f_e * (0.50 + 0.63)                                  # geregelte Pumpe (Tab. 11)
        w_circ_pump_year = (p_hydr_w / 1000.0) * 365.0 * z * e_aux  # kWh/a (Gl. 16/17)

    # Heizungsumwälzpumpe: Auslegung (Teil 5, 6.3.2)
    dtheta_design = em["theta_design_vl"] - em["theta_design_rl"]
    v_flow_h = phi_max / (1.15 * max(dtheta_design, 1.0))           # Gl. (58) [m³/h]
    l_max_h = 2.0 * (l_char + b_char / 2.0 + n_storeys * room_height + 10.0)  # Gl. (60)
    dp_h = 0.13 * l_max_h + 2.0 + (25.0 if emission_key == "floor" else 0.0) + 1.0  # Gl. (59)
    if heating_system == "gas" and p_n < 35.0:
        dp_h += 20.0 * v_flow_h ** 2                                # Brennwert-Wärmetauscher
    p_hydr_h = max(0.2778 * dp_h * v_flow_h, 1.0)                   # Gl. (57) [W]
    f_e_h = 1.25 + math.sqrt(200.0 / p_hydr_h)                      # Gl. (62)

    # Lüftung: Ventilator-Hilfsenergie (Teil 6, Gl. 60)
    spi = (vent["spi_dc"] if fan_dc else vent["spi_ac"])
    w_fan_year = 0.001 * spi * N_MECH * volume * 24.0 * 365.0 if vent_key != "none" else 0.0

    # ------------------------------------------------------------------
    # Monatsschleife
    # ------------------------------------------------------------------
    sums = {k: 0.0 for k in
            ("q_hb", "q_hce", "q_hd", "q_hs", "q_rlt", "q_h_outg", "q_h_gen_loss", "q_h_f",
             "q_wb", "q_wd", "q_ws", "q_w_outg", "q_w_gen_loss", "q_w_f",
             "w_pump_h", "w_boiler_aux", "el_hp_h", "el_hp_w", "q_district_loss")}
    monthly_out = []
    cop_h_months: List[float] = []

    for m in range(12):
        days = MONTH_DAYS[m]
        t_month_h = days * 24.0
        theta_e = THETA_E[m]
        q_hb = float(monthly[m].get("q_heat", 0.0))
        eta_m = float(monthly[m].get("eta", 0.0)) or 0.95
        heating = q_hb > 0.0
        theta_cellar = THETA_I_UNHEATED if heating else 22.0        # Tab. 7/24

        # --- TWW-Nutzenergie im Monat ---
        q_wb = q_wb_year / 365.0 * days
        if not is_residential:
            q_wb = q_wb_year * (days * profile["usage_days"] / 365.0) / profile["usage_days"]

        # ---------- Heizung: Übergabe (Gl. 34) ----------
        q_hce = q_hb * em["delta_theta_ce"] / max(theta_i - theta_e, 1.0) if heating else 0.0

        # ---------- Heizung: Verteilung (Gl. 52) ----------
        q_hd = q_hd_recov = 0.0
        beta_d = 0.0
        if heating:
            beta_d = min((q_hb + q_hce) * f_hydr / (phi_max * t_month_h), 1.0)
            theta_hk = _theta_hk_av(beta_d, em)
            loss_v = U_PIPE_V * lh["v"] * (theta_hk - (theta_i if pipes_inside else THETA_I_UNHEATED))
            loss_sa = U_PIPE_SA * (lh["s"] + lh["a"]) * (theta_hk - theta_i)
            loss_v = max(loss_v, 0.0)
            loss_sa = max(loss_sa, 0.0)
            q_hd_gross = (loss_v + loss_sa) * t_month_h / 1000.0
            # rückgewinnbar: Leitungen im beheizten Bereich (S/A immer, V optional)
            recov_share = (loss_sa + (loss_v if pipes_inside else 0.0)) / max(loss_v + loss_sa, 1e-9)
            q_hd_recov = q_hd_gross * recov_share * eta_m
            q_hd = q_hd_gross - q_hd_recov

        # ---------- Heizung: Pufferspeicher (Pellet) ----------
        q_hs = 0.0
        if heating and v_buffer > 0:
            q_hs_gross = ((THETA_S_AV - theta_i) / 45.0) * days * q_buf_p0_day * 1.2
            q_hs = q_hs_gross * (1.0 - eta_m)        # Aufstellung beheizt → großteils nutzbar

        # ---------- RLT-Luftaufbereitung (Teil 3): Zuluft auf Raumtemperatur ----------
        # Q_RLT = n_rlt · V · c_Luft · (θ_i − θ_e) · t   [kWh]; geht über denselben Erzeuger.
        q_rlt = (n_rlt * volume * 0.34 * max(theta_i - theta_e, 0.0) * t_month_h / 1000.0
                 if n_rlt > 0 else 0.0)

        q_h_outg = q_hb + q_hce + q_hd + q_hs + q_rlt

        # ---------- TWW: Verteilung (Teil 8, Gl. 13/14) ----------
        theta_w_free = 25.0 * U_PIPE_SA ** -0.2      # ≈ 32,9 °C (ohne Zirkulation)
        amb_in = theta_i if heating else 22.0
        if with_circ:
            z_h = min(10.0 + 1.0 / (0.07 + 50.0 / bgf), 24.0)
            loss_circ = (U_PIPE_V * lw["v"] * (THETA_W_CIRC - theta_cellar)
                         + U_PIPE_SA * lw["s"] * (THETA_W_CIRC - amb_in)) * z_h
            loss_rest = (U_PIPE_V * lw["v"] / 2.0 * (theta_w_free - theta_cellar)
                         + U_PIPE_SA * lw["s"] / 2.0 * (theta_w_free - amb_in)) * (24.0 - z_h)
            loss_a = U_PIPE_SA * lw["a"] * (theta_w_free - amb_in) * 24.0
            q_wd_gross = max(loss_circ + loss_rest + loss_a, 0.0) * days / 1000.0
            in_zone_share = (lw["s"] + lw["a"]) / max(lw["v"] + lw["s"] + lw["a"], 1e-9)
        else:
            loss = (U_PIPE_V * lw["v"] * max(theta_w_free - theta_cellar, 0.0)
                    + U_PIPE_SA * (lw["s"] + lw["a"]) * max(theta_w_free - amb_in, 0.0)) * 24.0
            q_wd_gross = loss * days / 1000.0
            in_zone_share = (lw["s"] + lw["a"]) / max(lw["v"] + lw["s"] + lw["a"], 1e-9)
        q_wd_recov = q_wd_gross * in_zone_share * (eta_m if heating else 0.0)
        q_wd = q_wd_gross - q_wd_recov

        # ---------- TWW: Speicher (Gl. 25) ----------
        amb_storage = theta_i if storage_inside else theta_cellar
        q_ws_gross = 1.2 * ((THETA_S_AV - amb_storage) / 45.0) * days * q_s_p0_day
        q_ws_recov = q_ws_gross * (eta_m if (heating and storage_inside) else 0.0)
        q_ws = q_ws_gross - q_ws_recov

        q_w_outg = q_wb + q_wd + q_ws

        # ---------- Erzeugung ----------
        q_h_gen_loss = q_w_gen_loss = 0.0
        el_hp_h = el_hp_w = 0.0
        q_district_loss = 0.0
        w_boiler_aux = 0.0
        t_w_pn_day = 0.0

        if boiler:
            # Tageslaufzeit TWW bei Nennlast (Teil 8, Gl. 107)
            t_w_pn_day = min(q_w_outg / (p_n * days), 20.0) if p_n > 0 else 0.0
            theta_rl = _theta_rl_av(beta_d, em) if heating else 30.0
            theta_op = _theta_hk_av(beta_d, em) if heating else 50.0
            ref = theta_rl if boiler["condensing"] else theta_op
            eta_pn = eta_k_pn + boiler["K"] * (70.0 - theta_op)                 # Gl. (185)
            eta_pint = eta_k_pint + boiler["L"] * (boiler["theta_test_pint"] - ref)  # Gl. (186)
            theta_gen_amb = theta_i                       # Aufstellung beheizt (Standard)
            theta_gen_av = theta_op if heating else (50.0 if with_circ else 40.0)
            q_p0_theta = q_p0_70 * max(theta_gen_av - theta_gen_amb, 0.0) / 50.0    # Gl. (184)

            p_gen_p0 = q_p0_theta * (p_n / eta_k_pn) * f_hs_hi                  # Gl. (183)
            p_gen_pint = max((f_hs_hi - eta_pint) / eta_pint, 0.0) * BETA_PINT * p_n  # Gl. (187)
            p_gen_pn = max((f_hs_hi - eta_pn) / eta_pn, 0.0) * p_n              # Gl. (188)

            if heating:
                t_h_day = 24.0 - t_w_pn_day
                p_d_in = q_h_outg / (days * max(t_h_day, 1.0))                  # Gl. (181)
                beta_gen = min(p_d_in / p_n, 1.0)                               # Gl. (154)
                if beta_gen <= BETA_PINT:                                       # Gl. (179)
                    loss_day = (beta_gen / BETA_PINT) * (p_gen_pint - p_gen_p0) + p_gen_p0
                else:                                                           # Gl. (180)
                    loss_day = ((beta_gen - BETA_PINT) / (1.0 - BETA_PINT)
                                * (p_gen_pn - p_gen_pint) + p_gen_pint)
                q_h_gen_gross = max(loss_day, 0.0) * t_h_day * days             # Gl. (178)
                # rückgewinnbare Strahlungsverluste (Gl. 189–191), Aufstellung beheizt
                q_s_theta = (0.75 if heating_system == "pellet" else 0.5) * q_p0_theta
                q_recov = q_s_theta * (p_n / eta_k_pn) * t_h_day * days * eta_m
                q_h_gen_loss = max(q_h_gen_gross - q_recov, 0.0)
            else:
                # Standby außerhalb der Heizzeit nur für TWW-Bereitschaft
                q_w_gen_loss += p_gen_p0 * (24.0 - t_w_pn_day) * days

            # TWW-Erzeugung bei Nennlast (Teil 8, 6.4.12, Gl. 102–105)
            eta_pn_w = eta_k_pn + boiler["K"] * (50.0 - THETA_S_AV)             # Gl. (105)
            q_w_gen_loss += max(f_hs_hi / max(eta_pn_w, 0.1) - 1.0, 0.0) * q_w_outg

            # Hilfsenergie Kessel (Gl. 111/220)
            p_aux_pn = (AUX_BOILER_PN[0] + AUX_BOILER_PN[1] * p_n ** AUX_BOILER_PN[2]) / 1000.0
            p_aux_p0 = (AUX_BOILER_P0[0] + AUX_BOILER_P0[1] * p_n ** AUX_BOILER_P0[2]) / 1000.0
            # Brennerlaufzeit [h/d]: Wärmemenge / Nennleistung (kWh / (d·kW) = h/d)
            run_h_day = t_w_pn_day + (q_h_outg / (days * p_n) if heating and p_n > 0 else 0.0)
            run_h_day = min(run_h_day, 24.0)
            w_boiler_aux = (p_aux_pn * run_h_day + p_aux_p0 * (24.0 - run_h_day)) * days

            q_h_f = q_h_outg + q_h_gen_loss
            q_w_f = q_w_outg + q_w_gen_loss

        elif heating_system == "heatpump":
            theta_vl = (_theta_hk_av(beta_d, em) + dtheta_design / 2.0) if heating else em["theta_design_vl"]
            cop_h = eta_g * (theta_vl + 273.15) / max(theta_vl - theta_e, 5.0)
            cop_h = min(max(cop_h, 1.0), COP_CAP)
            cop_w = eta_g * (THETA_S_AV + 273.15) / max(THETA_S_AV - theta_e, 10.0)
            cop_w = min(max(cop_w, 1.0), COP_CAP)
            el_hp_h = q_h_outg / cop_h
            el_hp_w = q_w_outg / cop_w
            if heating:
                cop_h_months.append(cop_h)
            q_h_f = q_w_f = 0.0     # Endenergie ist Strom (separat bilanziert)

        else:  # district
            q_district_loss = h_ds * (theta_ds - THETA_I_UNHEATED) * days / 365.0   # Gl. (242)
            q_h_f = q_h_outg + q_district_loss    # Stationsverluste der Heizung zugeordnet
            q_w_f = q_w_outg

        # ---------- Heizungspumpe (Gl. 56/61) ----------
        w_pump_h = 0.0
        if heating and phi_max > 0:
            e_aux_h = f_e_h * (0.90 + 0.10 / max(beta_d, 0.05))    # Δp variabel (Tab. 28)
            w_pump_h = (p_hydr_h / 1000.0) * beta_d * t_month_h * e_aux_h

        # ---------- Summen ----------
        vals = {"q_hb": q_hb, "q_hce": q_hce, "q_hd": q_hd, "q_hs": q_hs, "q_rlt": q_rlt,
                "q_h_outg": q_h_outg, "q_h_gen_loss": q_h_gen_loss,
                "q_h_f": q_h_f if heating_system != "heatpump" else 0.0,
                "q_wb": q_wb, "q_wd": q_wd, "q_ws": q_ws, "q_w_outg": q_w_outg,
                "q_w_gen_loss": q_w_gen_loss,
                "q_w_f": q_w_f if heating_system != "heatpump" else 0.0,
                "w_pump_h": w_pump_h, "w_boiler_aux": w_boiler_aux,
                "el_hp_h": el_hp_h, "el_hp_w": el_hp_w,
                "q_district_loss": q_district_loss}
        for k, v in vals.items():
            sums[k] += v

        monthly_out.append({"month": MONTH_NAMES[m], "q_hb": round(q_hb, 1),
                            "q_h_outg": round(q_h_outg, 1), "q_w_outg": round(q_w_outg, 1)})

    # ------------------------------------------------------------------
    # Jahresbilanz / Energieträger
    # ------------------------------------------------------------------
    aux_electricity = (sums["w_pump_h"] + sums["w_boiler_aux"]
                       + w_circ_pump_year + w_fan_year)

    # --- Beleuchtung (Teil 4, nur Nichtwohngebäude) -------------------------------
    lighting = {"applicable": False, "q_lf_kwh": 0.0}
    if not is_residential:
        lighting = calculate_lighting(
            profile_key, bgf,
            lamp=str(data.get("lighting_lamp", "led_leuchte")),
            presence_control=bool(data.get("lighting_presence_control", False)),
            daylight=str(data.get("lighting_daylight", "manual")),
            daylight_share=safe_float(data.get("lighting_daylight_share"), 0.5),
            light_type=str(data.get("lighting_type", "direkt")),
        )
    lighting_end = lighting.get("q_lf_kwh", 0.0)

    if heating_system == "heatpump":
        heating_end = sums["el_hp_h"]
        hotwater_end = sums["el_hp_w"]
        carrier = "electricity"
        fuel_end = 0.0
        electricity_end = heating_end + hotwater_end + aux_electricity + lighting_end
        jaz = ((sums["q_h_outg"] + sums["q_w_outg"])
               / max(heating_end + hotwater_end, 1e-9))
    else:
        # Brennstoffe: Kette ist Hs-bezogen → Umrechnung auf Hi (GEG-Faktorbezug)
        f = F_HS_HI.get(heating_system, 1.0)
        heating_end = sums["q_h_f"] / f
        hotwater_end = sums["q_w_f"] / f
        carrier = heating_system if heating_system != "gas" else "gas"
        fuel_end = heating_end + hotwater_end
        electricity_end = aux_electricity + lighting_end
        jaz = None

    # --- Kühlung (Teil 7): Nutzkälte über elektrische Kältemaschine (EER) ---
    cooling_eer = safe_float(data.get("cooling_eer"), 3.0) or 3.0
    cooling_end = cooling_demand_year / cooling_eer if cooling_demand_year > 0 else 0.0
    electricity_end += cooling_end          # Kälteerzeugung ist immer Strom

    # Heizungs-Endenergie in Raum- und RLT-Anteil aufteilen (nur Darstellung)
    rlt_share = sums["q_rlt"] / sums["q_h_outg"] if sums["q_h_outg"] > 0 else 0.0
    heating_rlt_end = heating_end * rlt_share
    heating_space_end = heating_end - heating_rlt_end

    total_end = (heating_end + hotwater_end + aux_electricity + lighting_end + cooling_end)
    carrier_key = {"gas": "gas", "pellet": "pellet", "district": "district",
                   "heatpump": "electricity"}[heating_system]
    primary = (fuel_end * F_PRIMARY[carrier_key] if heating_system != "heatpump" else 0.0) \
        + electricity_end * F_PRIMARY["electricity"] \
        + (0.0 if heating_system != "district" else 0.0)
    if heating_system == "district":
        primary = fuel_end * F_PRIMARY["district"] + electricity_end * F_PRIMARY["electricity"]
    co2 = (fuel_end * F_CO2[carrier_key] if heating_system != "heatpump" else 0.0) \
        + electricity_end * F_CO2["electricity"]

    spec_end = total_end / bgf
    spec_primary = primary / bgf

    from ..constants import SYSTEM_RATING_THRESHOLDS
    if spec_primary <= SYSTEM_RATING_THRESHOLDS["efficient"]:
        label, color, msg = "Sehr effizient", "green", "Die Anlagentechnik arbeitet energetisch günstig."
    elif spec_primary <= SYSTEM_RATING_THRESHOLDS["medium"]:
        label, color, msg = "Mittel", "yellow", "Die Anlagentechnik ist nutzbar, aber optimierbar."
    else:
        label, color, msg = "Verbesserungsbedarf", "red", "Die Anlagentechnik verursacht hohe Primärenergieverbräuche."

    return {
        "ok": True,
        # --- Frontend-kompatible Kernfelder ---
        "heating_end_energy": round(heating_end, 2),
        "heating_space_end_energy": round(heating_space_end, 2),   # „Heizen Raum"
        "heating_rlt_end_energy": round(heating_rlt_end, 2),       # „Heizen RLT" (Teil 3)
        "hotwater_end_energy": round(hotwater_end, 2),
        "lighting_end_energy": round(lighting_end, 2),
        "auxiliary_electricity": round(aux_electricity, 2),
        "cooling_demand_kwh": round(cooling_demand_year, 1),       # Nutzkälte Q_c,b (Teil 2)
        "cooling_end_energy": round(cooling_end, 2),               # „Kühlen Raum" Endenergie
        "cooling_eer": cooling_eer,
        "total_end_energy": round(total_end, 2),
        "primary_energy": round(primary, 2),
        "co2_emissions": round(co2, 2),
        "specific_end_energy": round(spec_end, 2),
        "specific_primary_energy": round(spec_primary, 2),
        # Lüftung ist jetzt Teil der Monatsbilanz – keine Gradstunden-Doppelzählung mehr.
        "ventilation_loss_kwh": 0.0,
        "adjusted_heat_demand_net": round(q_hb_year, 2),
        "system_label": label, "system_color": color, "system_message": msg,
        # --- DIN-Detailkennwerte (Stufe 2) ---
        "din": {
            "basis": basis,
            "heating_system": heating_system,
            "emission_label": em["label"],
            "n_eff_air_change": round(n_eff, 3),
            "ventilation_label": vent["label"],
            "phi_max_kw": round(phi_max, 2),
            "p_n_kw": round(p_n, 1),
            "q_h_b": round(sums["q_hb"], 1),
            "q_h_ce": round(sums["q_hce"], 1),
            "q_h_d": round(sums["q_hd"], 1),
            "q_h_s": round(sums["q_hs"], 1),
            "q_rlt": round(sums["q_rlt"], 1),                 # RLT-Luftaufbereitung (Teil 3)
            "cooling_setpoint": cooling_setpoint,
            "cooling_demand_kwh": round(cooling_demand_year, 1),
            "q_h_outg": round(sums["q_h_outg"], 1),
            "q_h_gen_loss": round(sums["q_h_gen_loss"], 1),
            "q_w_b": round(sums["q_wb"], 1),
            "q_w_d": round(sums["q_wd"], 1),
            "q_w_s": round(sums["q_ws"], 1),
            "q_w_outg": round(sums["q_w_outg"], 1),
            "q_w_gen_loss": round(sums["q_w_gen_loss"], 1),
            "district_station_loss": round(sums["q_district_loss"], 1),
            "aux_pump_heating": round(sums["w_pump_h"], 1),
            "aux_boiler": round(sums["w_boiler_aux"], 1),
            "aux_circulation_pump": round(w_circ_pump_year, 1),
            "aux_fans": round(w_fan_year, 1),
            "dhw_storage_liters": round(v_storage, 0),
            "dhw_circulation": with_circ,
            "jaz": round(jaz, 2) if jaz else None,
            "pipe_lengths_heating_m": {k: round(v, 1) for k, v in lh.items()},
            "pipe_lengths_dhw_m": {k: round(v, 1) for k, v in lw.items()},
            "lighting": lighting,
            "monthly": monthly_out,
            "calculation_basis": "DIN V 18599-4/-5/-6/-8:2018-09 (Standardwerte)",
        },
    }
