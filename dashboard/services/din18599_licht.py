"""
DIN V 18599-4 – Beleuchtung (Tabellenverfahren, 5.4.2) für Nichtwohngebäude.

Endenergie (Gl. 1–6):
    Q_l,f = F_t · p · [A_TL·(t_Tag·F_TL·F_Prä + t_Nacht·F_Prä) + A_KTL·(t_Tag + t_Nacht)·F_Prä]
    p     = p_j,lx(k, Beleuchtungsart) · E_m · k_A · k_Lampe        [W/m²]
    F_Prä = 1 − F_A · C_Prä,kon   (Gl. 40; Tab. 28: ohne Melder 0,5 / mit 0,95)

Quellen: Tabelle 5 (p_j,lx je Raumindex), Lampenart-Korrekturen (Tab. 6),
Nutzungsrandbedingungen aus DIN V 18599-10 Anhang A (E_m, k, k_A, F_A, t_Tag/t_Nacht, F_t).
Dokumentierte Vereinfachung: Tageslicht-Teilbetriebsfaktor F_TL als Anhaltswert je
Kontrollart statt des detaillierten C_TL-Verfahrens (5.5).
"""
from __future__ import annotations

from typing import Any, Dict

# Tabelle 5: p_j,lx [W/(m²·lx)] über Raumindex k, je Beleuchtungsart (Leuchtstoff EVG)
_K_AXIS = [0.6, 0.7, 0.8, 0.9, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
_P_JLX = {
    "direkt":          [0.045, 0.041, 0.037, 0.035, 0.033, 0.029, 0.027, 0.025, 0.024, 0.023, 0.022, 0.021],
    "direkt_indirekt": [0.067, 0.059, 0.053, 0.049, 0.045, 0.039, 0.036, 0.032, 0.029, 0.028, 0.026, 0.025],
    "indirekt":        [0.122, 0.105, 0.090, 0.080, 0.071, 0.058, 0.050, 0.044, 0.039, 0.037, 0.035, 0.033],
}

# Lampenart-Korrekturfaktoren (Teil 4, Tab. 6; Bezug Leuchtstoff stabförmig EVG = 1,0)
LAMP_FACTORS = {
    "led_leuchte": {"label": "LED-Leuchte", "k": 0.49},
    "led_ersatz":  {"label": "LED-Ersatzlampe (Retrofit)", "k": 0.53},
    "lsl_t5":      {"label": "Leuchtstoff T5, EVG, effizient", "k": 0.80},
    "lsl_evg":     {"label": "Leuchtstofflampe, EVG", "k": 1.00},
    "kompakt":     {"label": "Kompaktleuchtstoff, EVG", "k": 1.20},
}

# Tageslicht-Teilbetriebsfaktor F_TL (vereinfachte Anhaltswerte; detailliertes
# C_TL-Verfahren nach 5.5 als späterer Ausbau)
DAYLIGHT_FACTORS = {
    "dimmed":   {"label": "tageslichtabhängig gedimmt", "f_tl": 0.55},
    "switched": {"label": "tageslichtabhängig geschaltet", "f_tl": 0.70},
    "manual":   {"label": "manuell geschaltet", "f_tl": 0.80},
    "none":     {"label": "kein Tageslicht (innenliegend)", "f_tl": 1.00},
}

# Beleuchtungs-Nutzungsrandbedingungen je Profil (DIN V 18599-10 Anhang A)
LIGHT_PROFILES: Dict[str, Dict[str, Any]] = {
    "einzelbuero":    {"em": 500, "k": 0.9,  "k_a": 0.84, "f_a": 0.30, "t_day": 2543, "t_night": 207, "f_t": 0.7},
    "gruppenbuero":   {"em": 500, "k": 1.25, "k_a": 0.92, "f_a": 0.30, "t_day": 2543, "t_night": 207, "f_t": 0.7},
    "grossraumbuero": {"em": 500, "k": 2.5,  "k_a": 0.93, "f_a": 0.00, "t_day": 2543, "t_night": 207, "f_t": 1.0},
    "besprechung":    {"em": 500, "k": 1.25, "k_a": 0.93, "f_a": 0.50, "t_day": 2543, "t_night": 207, "f_t": 1.0},
    "klassenzimmer":  {"em": 300, "k": 2.0,  "k_a": 0.97, "f_a": 0.25, "t_day": 1400, "t_night": 0,   "f_t": 0.9},
}


def _p_jlx(k: float, art: str) -> float:
    """Tabelle 5 mit linearer Interpolation über den Raumindex k."""
    values = _P_JLX.get(art, _P_JLX["direkt"])
    k = max(min(k, _K_AXIS[-1]), _K_AXIS[0])
    for i in range(len(_K_AXIS) - 1):
        if _K_AXIS[i] <= k <= _K_AXIS[i + 1]:
            t = (k - _K_AXIS[i]) / (_K_AXIS[i + 1] - _K_AXIS[i])
            return values[i] + t * (values[i + 1] - values[i])
    return values[-1]


def calculate_lighting(profile_key: str, area_m2: float,
                       lamp: str = "led_leuchte",
                       presence_control: bool = False,
                       daylight: str = "manual",
                       daylight_share: float = 0.5,
                       light_type: str = "direkt") -> Dict[str, Any]:
    """Endenergie Beleuchtung Q_l,f für eine NWG-Zone (Tabellenverfahren)."""
    lp = LIGHT_PROFILES.get(profile_key)
    if lp is None or area_m2 <= 0:
        return {"applicable": False, "q_lf_kwh": 0.0}

    lamp_data = LAMP_FACTORS.get(lamp, LAMP_FACTORS["led_leuchte"])
    p = _p_jlx(lp["k"], light_type) * lp["em"] * lp["k_a"] * lamp_data["k"]   # W/m²

    c_pra_kon = 0.95 if presence_control else 0.5                  # Tab. 28
    f_prae = 1.0 - lp["f_a"] * c_pra_kon                           # Gl. (40)
    f_tl = DAYLIGHT_FACTORS.get(daylight, DAYLIGHT_FACTORS["manual"])["f_tl"]
    share = max(min(daylight_share, 1.0), 0.0)

    t_eff = (share * (lp["t_day"] * f_tl * f_prae + lp["t_night"] * f_prae)
             + (1.0 - share) * (lp["t_day"] + lp["t_night"]) * f_prae)        # Gl. (4)–(6)
    q_lf = lp["f_t"] * p * area_m2 * t_eff / 1000.0                # kWh/a (Gl. 1/2)

    return {
        "applicable": True,
        "q_lf_kwh": round(q_lf, 1),
        "q_lf_specific": round(q_lf / area_m2, 2),
        "p_w_m2": round(p, 2),
        "lamp_label": lamp_data["label"],
        "daylight_label": DAYLIGHT_FACTORS.get(daylight, DAYLIGHT_FACTORS["manual"])["label"],
        "f_prae": round(f_prae, 3),
        "em_lx": lp["em"],
        "basis": "DIN V 18599-4:2018-09, Tabellenverfahren (5.4.2)",
    }
