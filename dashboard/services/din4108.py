"""
DIN 4108 – Wärmeschutz und Energie-Einsparung in Gebäuden.

Ergänzt die energetische Bilanz nach DIN V 18599 um die bauphysikalischen
Nachweise/Anforderungen der DIN 4108. Alle hinterlegten Tabellenwerte und
Formeln wurden direkt aus den Normteilen verifiziert (siehe
docs/DIN4108_Umsetzung.md):

- Feature 1 – Mindestwärmeschutz von Bauteilen: DIN 4108-2:2026-05, §5, Tabelle 3
- Feature 2 – Sommerlicher Wärmeschutz (Sonneneintragskennwert):
             DIN 4108-2:2026-05, §8.4, Tabelle 8 (+ Tab. 7 Verzicht, Tab. 10–13 F_C)
- Feature 3 – Tauwassernachweis (Periodenbilanz-/Glaser-Verfahren):
             DIN 4108-3:2024-03, §5.2 + Anhang A (Klima Tab. A.3) + Anhang C (Formeln);
             Stoff-Bemessungswerte λ/μ: DIN 4108-4:2020-11, Tabelle 1 + 2
- Feature 4 – Wärmebrücken-Zuschlag: DIN 4108 Beiblatt 2:2019-06, §5.2/5.4/5.5
             (ΔU_WB nach DIN V 18599-2) + Luftdichtheit n50: DIN 4108-7:2026-04, §5

Konventionen wie im DIN-V-18599-Code: deutsche Norm-Symbolik, Rückgabe als dict
mit `ok`/`errors`, Ampel-Bewertung (label/color), Werte gerundet für JSON.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from ..utils import safe_float

# Wärmeübergangswiderstände (DIN EN ISO 6946, Standard) für U-/R-Umrechnung.
DEFAULT_R_SI = 0.13   # m²K/W, Wärmestrom horizontal (Wand)
DEFAULT_R_SE = 0.04   # m²K/W, außen

# ===========================================================================
# FEATURE 1 — Mindestwärmeschutz von Bauteilen (DIN 4108-2:2026-05, Tab. 3)
# ===========================================================================
# Mindestwerte des Wärmedurchlasswiderstands R_min [m²·K/W] je Bauteiltyp.
# Schlüssel = Frontend-Typ; Werte exakt aus Tabelle 3 (Zeilen 1–13).
MINDEST_R = {
    "aussenwand":                  {"r_min": 1.20, "label": "Wand, beheizter Raum (gegen Außenluft/Erdreich/unbeheizt)"},
    "aussenwand_niedrig":          {"r_min": 0.55, "label": "Wand, niedrig beheizter Raum"},
    "dachschraege":                {"r_min": 1.20, "label": "Dachschräge gegen Außenluft"},
    "flachdach":                   {"r_min": 1.20, "label": "Decke nach oben / Flachdach gegen Außenluft"},
    "decke_oben_belueftet":        {"r_min": 0.90, "label": "Decke zu belüftetem Raum (Dachschräge/Abseite)"},
    "decke_oben_unbeheizt":        {"r_min": 0.90, "label": "Decke zu nicht beheiztem / bekriechbarem Raum"},
    "decke_dachschraege_gedaemmt": {"r_min": 0.35, "label": "Decke zwischen gedämmten Dachschrägen/Abseiten"},
    "decke_unten_aussen":          {"r_min": 1.75, "label": "Decke nach unten gegen Außenluft/Tiefgarage/Durchfahrt"},
    "decke_unten_keller":          {"r_min": 0.90, "label": "Decke gegen nicht beheizten Kellerraum"},
    "bodenplatte_erdreich":        {"r_min": 0.90, "label": "Sohlplatte ans Erdreich (bis 5 m Raumtiefe)"},
    "boden_hohlraum_erdreich":     {"r_min": 0.90, "label": "Boden über nicht belüftetem Hohlraum ans Erdreich"},
    "trennwand_wohnung":           {"r_min": 0.07, "label": "Wohnungs-/Gebäudetrennwand, Trennwand Treppenraum"},
    "trenndecke_wohnung":          {"r_min": 0.35, "label": "Wohnungstrenndecke / Decke zw. versch. Nutzung"},
}
# Sonderfall: Bauteile mit flächenbezogener Masse m' < 100 kg/m² → R ≥ 1,75 (§5.1.1).
R_MIN_LEICHTBAUTEIL = 1.75
# Opake Ausfachung transparenter Bauteile → R ≥ 1,2 (U_p ≤ 0,73) (§5.1.2).
R_MIN_OPAKE_AUSFACHUNG = 1.20


def _r_from_input(R: float, U: float, r_si: float, r_se: float) -> Optional[float]:
    """Wärmedurchlasswiderstand R des Bauteils (ohne Übergänge) bestimmen.
    Direkt aus R, sonst aus U via R = 1/U − R_si − R_se (DIN EN ISO 6946)."""
    if R > 0:
        return R
    if U > 0:
        r = 1.0 / U - r_si - r_se
        return r if r > 0 else 0.0
    return None


def pruefe_mindestwaermeschutz(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mindestwärmeschutz-Nachweis je Bauteil (DIN 4108-2:2026-05, §5, Tab. 3).

    data["bauteile"]: Liste von dicts mit
        name, typ (Schlüssel aus MINDEST_R), R [m²K/W] ODER u [W/m²K],
        flaechenmasse [kg/m²] (optional), opake_ausfachung (bool, optional),
        inhomogen (bool, optional) + gefach_r [m²K/W] (Holzständer-Gefach).
    """
    errors: List[str] = []
    bauteile = data.get("bauteile") or []
    if not isinstance(bauteile, list) or not bauteile:
        return {"ok": False, "errors": ["Keine Bauteile zum Prüfen übergeben."]}

    r_si = safe_float(data.get("r_si"), DEFAULT_R_SI) or DEFAULT_R_SI
    r_se = safe_float(data.get("r_se"), DEFAULT_R_SE) or DEFAULT_R_SE

    ergebnisse: List[Dict[str, Any]] = []
    alle_erfuellt = True
    for i, bt in enumerate(bauteile):
        name = str(bt.get("name") or f"Bauteil {i + 1}")
        typ = str(bt.get("typ") or "aussenwand")
        info = MINDEST_R.get(typ, MINDEST_R["aussenwand"])
        R = safe_float(bt.get("R") or bt.get("r"), 0.0)
        U = safe_float(bt.get("u") or bt.get("U"), 0.0)
        r_bauteil = _r_from_input(R, U, r_si, r_se)
        if r_bauteil is None:
            errors.append(f"{name}: weder R noch U-Wert angegeben.")
            continue

        # Maßgeblichen Mindestwert ermitteln (Tabellenwert + Sonderfälle §5.1).
        r_min = info["r_min"]
        hinweise: List[str] = []
        if bool(bt.get("opake_ausfachung")):
            r_min = max(r_min, R_MIN_OPAKE_AUSFACHUNG)
            hinweise.append("opake Ausfachung → R ≥ 1,2 (U_p ≤ 0,73 W/m²K)")
        flaechenmasse = safe_float(bt.get("flaechenmasse"), 0.0)
        if 0 < flaechenmasse < 100 and r_min < R_MIN_LEICHTBAUTEIL:
            r_min = R_MIN_LEICHTBAUTEIL
            hinweise.append("m′ < 100 kg/m² → R ≥ 1,75 m²K/W")

        erfuellt = r_bauteil >= r_min - 1e-9
        # Thermisch inhomogen (Holzständer): zusätzlich Gefach R_G ≥ 1,75 (§5.1.1).
        gefach_ok = True
        if bool(bt.get("inhomogen")):
            gefach_r = safe_float(bt.get("gefach_r"), 0.0)
            gefach_ok = gefach_r >= 1.75 - 1e-9
            hinweise.append("inhomogen: Gefach R_G ≥ 1,75 und Bauteil R ≥ 1,0 erforderlich")
            erfuellt = erfuellt and gefach_ok and r_bauteil >= 1.0

        alle_erfuellt = alle_erfuellt and erfuellt
        ergebnisse.append({
            "name": name,
            "typ": typ,
            "typ_label": info["label"],
            "r_bauteil": round(r_bauteil, 3),
            "u_bauteil": round(1.0 / (r_bauteil + r_si + r_se), 3) if r_bauteil + r_si + r_se > 0 else None,
            "r_min": round(r_min, 3),
            "erfuellt": erfuellt,
            "color": "green" if erfuellt else "red",
            "reserve": round(r_bauteil - r_min, 3),
            "hinweise": hinweise,
        })

    if errors:
        return {"ok": False, "errors": errors}

    return {
        "ok": True,
        "calculation_basis": "DIN 4108-2:2026-05, Abschnitt 5 (Tabelle 3) – Mindestwärmeschutz",
        "bauteile": ergebnisse,
        "alle_erfuellt": alle_erfuellt,
        "anzahl": len(ergebnisse),
        "anzahl_erfuellt": sum(1 for e in ergebnisse if e["erfuellt"]),
        "rating_label": "Erfüllt" if alle_erfuellt else "Nicht erfüllt",
        "rating_color": "green" if alle_erfuellt else "red",
        "rating_message": (
            "Alle Bauteile erfüllen den Mindestwärmeschutz (Schimmel-/Tauwasserschutz)."
            if alle_erfuellt else
            "Mindestens ein Bauteil unterschreitet R_min → Gefahr von Tauwasser/Schimmel an der Innenoberfläche."
        ),
    }


# ===========================================================================
# FEATURE 2 — Sommerlicher Wärmeschutz (DIN 4108-2:2026-05, §8.4)
# ===========================================================================
# Tabelle 8 – Anteiliger Sonneneintragskennwert S1 (Nachtlüftung × Bauart),
# je Klimaregion (A/B/C) und Nutzung (Wohn/Nichtwohn).
# Struktur: S1[nachtlueftung][bauart] = {"wohn": (A,B,C), "nichtwohn": (A,B,C)}
S1_TABELLE = {
    "ohne": {
        "leicht": {"wohn": (0.071, 0.056, 0.041), "nichtwohn": (0.013, 0.007, 0.000)},
        "mittel": {"wohn": (0.080, 0.067, 0.054), "nichtwohn": (0.020, 0.013, 0.006)},
        "schwer": {"wohn": (0.087, 0.074, 0.061), "nichtwohn": (0.025, 0.018, 0.011)},
    },
    "erhoeht": {  # erhöhte Nachtlüftung n ≥ 2 h⁻¹
        "leicht": {"wohn": (0.098, 0.088, 0.078), "nichtwohn": (0.071, 0.060, 0.048)},
        "mittel": {"wohn": (0.114, 0.103, 0.092), "nichtwohn": (0.089, 0.081, 0.072)},
        "schwer": {"wohn": (0.125, 0.113, 0.101), "nichtwohn": (0.101, 0.092, 0.083)},
    },
    "hoch": {  # hohe Nachtlüftung n ≥ 5 h⁻¹
        "leicht": {"wohn": (0.128, 0.117, 0.105), "nichtwohn": (0.090, 0.082, 0.074)},
        "mittel": {"wohn": (0.160, 0.152, 0.143), "nichtwohn": (0.135, 0.124, 0.113)},
        "schwer": {"wohn": (0.181, 0.171, 0.160), "nichtwohn": (0.170, 0.158, 0.145)},
    },
}
# S2 (Fensterflächenanteil-Korrektur): S2 = a − b · f_wg  (Tab. 8, Zeile 10/11)
S2_KOEFF = {"wohn": (0.060, 0.231), "nichtwohn": (0.030, 0.115)}
REGION_INDEX = {"A": 0, "B": 1, "C": 2}
S3_SONNENSCHUTZGLAS = 0.03   # Zeile 12 (g ≤ 0,40), flächenanteilig
S4_NEIGUNG = -0.035          # Zeile 13, je f_neig (0°–60°)
S5_NORD = 0.10              # Zeile 14, je f_nord
S6_PASSIVE_KUEHLUNG = {"leicht": 0.02, "mittel": 0.04, "schwer": 0.06}  # Zeile 15–17

# Tabelle 7 – Verzicht auf Nachweis: zulässiger grundflächenbezogener
# Fensterflächenanteil f_wg [-] je Neigung/Orientierung.
NORD_ORIENT = {"north", "northeast", "northwest"}
# Abminderungsfaktoren F_C – Anhaltswerte (DIN 4108-2:2026-05, Tab. 10/11/13),
# Kategorie „allgemein" je Glaserzeugnis (zweifach/dreifach Verglasung).
FC_ANHALT = {
    "aussen":      {"label": "außenliegend (Rollladen/Jalousie/Markise)", "zweifach": 0.25, "dreifach": 0.24},
    "szr":         {"label": "im Scheibenzwischenraum (Isolierglas)",      "zweifach": 0.35, "dreifach": 0.31},
    "innen":       {"label": "innenliegend (Rollo/Plissee/Jalousie)",      "zweifach": 0.90, "dreifach": 0.95},
    "ohne":        {"label": "kein Sonnenschutz",                          "zweifach": 1.00, "dreifach": 1.00},
    "vordach":     {"label": "Vordach/Markise nicht parallel zum Glas",    "zweifach": 0.50, "dreifach": 0.50},
}


def _bauart_aus_cwirk(cwirk_spez: float) -> str:
    """Bauart aus wirksamer Wärmekapazität C_wirk/A_G [Wh/(K·m²)] (Tab. 8 Fußnote b)."""
    if cwirk_spez < 50:
        return "leicht"
    if cwirk_spez <= 130:
        return "mittel"
    return "schwer"


def berechne_sommerlicher_waermeschutz(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sonneneintragskennwert-Verfahren (DIN 4108-2:2026-05, §8.4).

    S_vorh = Σ(A_w,j · g_tot,j) / A_G  ≤  S_zul = ΣS_x
    """
    errors: List[str] = []
    a_g = safe_float(data.get("a_g"), 0.0)              # Nettogrundfläche Raum [m²]
    if a_g <= 0:
        errors.append("Nettogrundfläche A_G muss größer als 0 sein.")
    nutzung = "nichtwohn" if str(data.get("nutzung", "wohn")).startswith("nicht") else "wohn"
    region = str(data.get("klimaregion", "B")).upper()
    if region not in REGION_INDEX:
        errors.append("Klimaregion muss A, B oder C sein.")
    nachtlueftung = str(data.get("nachtlueftung", "ohne"))
    if nachtlueftung not in S1_TABELLE:
        nachtlueftung = "ohne"

    bauart = str(data.get("bauart", "")).strip().lower()
    cwirk_spez = safe_float(data.get("cwirk_spez"), 0.0)
    if bauart not in ("leicht", "mittel", "schwer"):
        bauart = _bauart_aus_cwirk(cwirk_spez) if cwirk_spez > 0 else "leicht"

    fenster = data.get("fenster") or []
    if not isinstance(fenster, list) or not fenster:
        errors.append("Mindestens ein Fenster muss angegeben werden.")
    if errors:
        return {"ok": False, "errors": errors}

    ridx = REGION_INDEX[region]
    # --- S_vorh + Flächenanteile -------------------------------------------
    a_w_gesamt = 0.0
    summe_a_gtot = 0.0
    a_w_nord = 0.0
    a_w_neig = 0.0
    a_w_sonnenschutzglas = 0.0
    fenster_out: List[Dict[str, Any]] = []
    for j, fe in enumerate(fenster):
        a_w = safe_float(fe.get("flaeche"), 0.0)
        if a_w <= 0:
            continue
        g = safe_float(fe.get("g"), 0.6)
        gtot = safe_float(fe.get("gtot"), 0.0)
        if gtot <= 0:
            fc = safe_float(fe.get("fc"), 1.0)
            fs = safe_float(fe.get("fs"), 1.0) or 1.0
            gtot = g * fc * fs
        orient = str(fe.get("orientierung", "south")).lower()
        neigung = safe_float(fe.get("neigung"), 90.0)   # ° gegenüber Horizontale
        selbstverschattet = bool(fe.get("selbstverschattet"))

        a_w_gesamt += a_w
        summe_a_gtot += a_w * gtot
        # S5: Nord/NO/NW mit Neigung > 60° oder dauerverschattet
        if (orient in NORD_ORIENT and neigung > 60) or selbstverschattet:
            a_w_nord += a_w
        # S4: Neigung 0°–60° gegenüber Horizontale
        if 0 <= neigung <= 60:
            a_w_neig += a_w
        # S3: Sonnenschutzglas g ≤ 0,40
        if g <= 0.40:
            a_w_sonnenschutzglas += a_w
        fenster_out.append({
            "index": j, "flaeche": round(a_w, 2), "g": round(g, 3),
            "gtot": round(gtot, 3), "orientierung": orient, "neigung": neigung,
            "beitrag": round(a_w * gtot, 3),
        })

    if a_w_gesamt <= 0:
        return {"ok": False, "errors": ["Gesamte Fensterfläche ist 0."]}

    s_vorh = summe_a_gtot / a_g
    f_wg = a_w_gesamt / a_g

    # --- S_zul = ΣS_x -------------------------------------------------------
    s1 = S1_TABELLE[nachtlueftung][bauart][nutzung][ridx]
    a_koeff, b_koeff = S2_KOEFF[nutzung]
    s2 = a_koeff - b_koeff * f_wg
    s3 = S3_SONNENSCHUTZGLAS * (a_w_sonnenschutzglas / a_w_gesamt)
    s4 = S4_NEIGUNG * (a_w_neig / a_w_gesamt)
    s5 = S5_NORD * (a_w_nord / a_w_gesamt)
    s6 = S6_PASSIVE_KUEHLUNG[bauart] if bool(data.get("passive_kuehlung")) else 0.0
    s_zul = s1 + s2 + s3 + s4 + s5 + s6

    erfuellt = s_vorh <= s_zul + 1e-9
    ausnutzung = (s_vorh / s_zul * 100.0) if s_zul > 0 else 999.0

    # --- Tabelle 7: Verzicht auf Nachweis möglich? -------------------------
    # Grenzwerte je nach (kleinster) Orientierung/Neigung der Raumfenster.
    grenze_pct = 7.0  # Neigung 0–60°: alle Orientierungen 7 %
    if all(safe_float(fe.get("neigung"), 90.0) > 60 for fe in fenster):
        # senkrechte Fenster: NW–Süd–NO 10 %, sonstige Nordorient. 15 %
        nur_nord = all(str(fe.get("orientierung", "")).lower() in NORD_ORIENT
                       for fe in fenster if safe_float(fe.get("flaeche"), 0) > 0)
        grenze_pct = 15.0 if nur_nord else 10.0
    verzicht_moeglich = (f_wg * 100.0) <= grenze_pct

    return {
        "ok": True,
        "calculation_basis": "DIN 4108-2:2026-05, §8.4 – Sonneneintragskennwertverfahren",
        "klimaregion": region,
        "nutzung": nutzung,
        "bauart": bauart,
        "nachtlueftung": nachtlueftung,
        "a_g": round(a_g, 2),
        "a_w_gesamt": round(a_w_gesamt, 2),
        "f_wg": round(f_wg, 4),
        "f_wg_prozent": round(f_wg * 100, 1),
        "s_vorh": round(s_vorh, 4),
        "s_zul": round(s_zul, 4),
        "anteile": {
            "S1_grund": round(s1, 4),
            "S2_fensteranteil": round(s2, 4),
            "S3_sonnenschutzglas": round(s3, 4),
            "S4_neigung": round(s4, 4),
            "S5_orientierung": round(s5, 4),
            "S6_passive_kuehlung": round(s6, 4),
        },
        "fenster": fenster_out,
        "erfuellt": erfuellt,
        "ausnutzung_prozent": round(ausnutzung, 1),
        "verzicht_moeglich": verzicht_moeglich,
        "verzicht_grenze_prozent": grenze_pct,
        "rating_label": "Erfüllt" if erfuellt else "Nicht erfüllt",
        "rating_color": "green" if erfuellt else "red",
        "rating_message": (
            f"S_vorh = {s_vorh:.3f} ≤ S_zul = {s_zul:.3f} → sommerlicher Wärmeschutz nachgewiesen."
            if erfuellt else
            f"S_vorh = {s_vorh:.3f} > S_zul = {s_zul:.3f} → Überhitzungsgefahr. "
            "Maßnahmen: besserer Sonnenschutz (kleineres F_C), kleinere Fenster, mehr Speichermasse, Nachtlüftung."
        ),
    }


# ===========================================================================
# FEATURE 3 — Tauwassernachweis / Periodenbilanzverfahren (Glaser)
#             DIN 4108-3:2024-03, §5.2 + Anhang A + Anhang C
# ===========================================================================
# Klimarandbedingungen Tabelle A.3.
GLASER_R_SI = 0.25   # m²K/W (Anhang A.2.2, abweichend von 6946-Standard)
GLASER_R_SE = 0.04
DELTA_0 = 2.0e-10    # kg/(m·s·Pa) – Diffusionsleitkoeffizient ruhende Luft (Anhang C, gerundet)
SD_LUFTSCHICHT = 0.01  # m – ruhende Luftschicht (A.2.3)
TAU_P_I = 1168.0     # Pa, Innenklima Tauperiode (20 °C / 50 %)
TAU_P_E = 321.0      # Pa, Außenklima Tauperiode (−5 °C / 80 %)
TAU_THETA_I = 20.0
TAU_THETA_E = -5.0
VERD_P_I = 1200.0    # Pa, Innen = Außen in der Verdunstungsperiode
VERD_P_E = 1200.0
VERD_PSAT_WAND = 1700.0   # Pa, Sättigungsdampfdruck im Tauwasserbereich (Wand/Decke/helles Dach)
VERD_PSAT_DACH_DUNKEL = 2000.0  # Pa, unverschattetes Dach mit dunkler Deckung
T_PERIODE_S = 7776e3  # s = 90 d, Dauer Tau- bzw. Verdunstungsperiode (Tab. A.3)

# Akzeptanzkriterien §5.2.2
MC_MAX_ALLG = 1.0    # kg/m² maximal zulässige Tauwassermasse (allgemein)
MC_MAX_GRENZ = 0.5   # kg/m² an Grenzflächen mit nicht kapillar saugender Schicht

# Temperaturfaktor-Kriterium f_Rsi (DIN 4108-2:2026-05, §6.2) — Schimmel-/
# Tauwasserfreiheit der Innenoberfläche. Randbedingungen (20 °C/50 %, −5 °C,
# R_si = 0,25) sind identisch mit der Tauperiode oben.
F_RSI_MIN = 0.70

# Bemessungswerte λ_B [W/(m·K)] und μ-Richtwerte aus DIN 4108-4:2020-11 (Tab. 1+2).
# μ als (trocken/feucht); im Glaser-Verfahren ist der für die Schichtposition
# ungünstigere Wert anzusetzen (Anhang A.2.3) – das Frontend bietet beide an.
# Repräsentative Auswahl gebräuchlicher Baustoffe (innen → außen einsetzbar).
MATERIAL_DB = [
    # (Schlüssel, Anzeigename, λ_B, μ_trocken, μ_feucht, Kategorie)
    ("gipsputz",        "Gipsputz",                       0.51, 4, 10,    "Putz/Estrich"),
    ("kalkzementputz",  "Kalk-/Kalkzementputz",           1.00, 15, 35,   "Putz/Estrich"),
    ("kunstharzputz",   "Kunstharzputz (außen)",          0.70, 50, 200,  "Putz/Estrich"),
    ("waermedaemmputz", "Wärmedämmputz (T1)",             0.12, 5, 20,    "Putz/Estrich"),
    ("zementestrich",   "Zementestrich",                  1.40, 15, 35,   "Putz/Estrich"),
    ("stahlbeton",      "Stahlbeton/Normalbeton",         2.30, 80, 130,  "Beton/Mauerwerk"),
    ("porenbeton",      "Porenbeton (ρ500)",              0.14, 5, 10,    "Beton/Mauerwerk"),
    ("leichtbeton",     "Leichtbeton (ρ800)",             0.39, 70, 150,  "Beton/Mauerwerk"),
    ("vollziegel",      "Vollziegel (ρ1800)",             0.81, 5, 10,    "Beton/Mauerwerk"),
    ("hochlochziegel",  "Hochlochziegel HLzW (ρ700)",     0.21, 5, 10,    "Beton/Mauerwerk"),
    ("klinker",         "Vollklinker (ρ1800)",            0.81, 50, 100,  "Beton/Mauerwerk"),
    ("kalksandstein",   "Kalksandstein (ρ1800)",          0.99, 15, 25,   "Beton/Mauerwerk"),
    ("mineralwolle",    "Mineralwolle (MW)",              0.035, 1, 1,    "Dämmstoff"),
    ("eps",             "EPS (Polystyrol expandiert)",    0.035, 20, 100, "Dämmstoff"),
    ("xps",             "XPS (Polystyrol extrudiert)",    0.035, 80, 250, "Dämmstoff"),
    ("pu",              "PU/PIR-Hartschaum",              0.025, 40, 200, "Dämmstoff"),
    ("holzfaser",       "Holzfaserdämmplatte (WF)",       0.040, 3, 5,    "Dämmstoff"),
    ("kork",            "Kork expandiert (ICB)",          0.045, 5, 10,   "Dämmstoff"),
    ("mineralschaum",   "Mineralschaum/Calciumsilikat",   0.045, 3, 6,    "Dämmstoff"),
    ("holz_nadel",      "Nadelholz (Konstruktionsholz)",  0.13, 20, 50,   "Holz"),
    ("osb",             "OSB-/Holzwerkstoffplatte",       0.13, 30, 50,   "Holz"),
    ("gipskarton",      "Gipskartonplatte",               0.25, 4, 10,    "Platte"),
    ("dampfbremse",     "Dampfbremse PE/PA (Folie)",      0.50, 50000, 50000, "Folie/Bahn"),
    ("bitumenbahn",     "Bitumen-Dachbahn",               0.17, 20000, 20000, "Folie/Bahn"),
    ("dampfbremse_var", "feuchtevar. Dampfbremse (sd~2m)", 0.50, 13000, 13000, "Folie/Bahn"),
]


def material_db() -> List[Dict[str, Any]]:
    """Material-Bemessungswerte (λ/μ) für den Glaser-Schichteditor."""
    return [{"key": k, "name": n, "lambda": lam, "mu_trocken": md, "mu_feucht": mf,
             "kategorie": kat} for (k, n, lam, md, mf, kat) in MATERIAL_DB]


def p_sat(theta: float) -> float:
    """Sättigungsdampfdruck [Pa] nach DIN 4108-3 Anhang C, Gl. (C.15)/(C.16)."""
    if theta >= 0:
        return 610.5 * math.exp(17.269 * theta / (237.3 + theta))
    return 610.5 * math.exp(21.875 * theta / (265.5 + theta))


def _lower_convex_hull(points: List[Tuple[float, float]]) -> List[int]:
    """Indizes der Stützpunkte der unteren konvexen Hülle (Andrew's monotone chain).

    Liefert beim Glaser-Diffusionsdiagramm exakt die Tauwasserebenen: die
    'straff gespannte' Dampfdruckgerade von innen nach außen, die unter der
    Sättigungskurve verläuft, knickt genau an den Kondensationsstellen ab.
    points: (s_d, p) sortiert nach s_d.
    """
    hull: List[int] = []
    for i in range(len(points)):
        while len(hull) >= 2:
            o, a, b = points[hull[-2]], points[hull[-1]], points[i]
            cross = (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
            if cross <= 1e-15:   # rechtsdrehend/kollinear → unterer Rand
                hull.pop()
            else:
                break
        hull.append(i)
    return hull


def berechne_tauwasser_glaser(data: Dict[str, Any]) -> Dict[str, Any]:
    """Periodenbilanzverfahren (Glaser), DIN 4108-3:2024-03, Anhang A.

    data["schichten"]: Liste innen→außen mit {name, d [m], lambda [W/mK], mu [-]}.
        Alternativ ruhende Luftschicht: {name, luftschicht: true, r [m²K/W]}.
    data["bauteil_typ"]: "wand" (Standard) oder "dach_dunkel".
    """
    errors: List[str] = []
    schichten = data.get("schichten") or []
    if not isinstance(schichten, list) or len(schichten) < 2:
        return {"ok": False, "errors": ["Mindestens zwei Schichten erforderlich."]}

    bauteil_typ = str(data.get("bauteil_typ", "wand"))
    verd_psat = VERD_PSAT_DACH_DUNKEL if bauteil_typ == "dach_dunkel" else VERD_PSAT_WAND

    # --- Schichten aufbereiten: R und s_d je Schicht -----------------------
    schicht_out: List[Dict[str, Any]] = []
    R_layers: List[float] = []
    sd_layers: List[float] = []
    for i, s in enumerate(schichten):
        name = str(s.get("name") or f"Schicht {i + 1}")
        if bool(s.get("luftschicht")):
            R = safe_float(s.get("r"), 0.0)
            sd = SD_LUFTSCHICHT
            d = safe_float(s.get("d"), 0.0)
            schicht_out.append({"name": name, "d": d, "lambda": None, "mu": None,
                                "r": round(R, 3), "sd": sd, "luftschicht": True})
        else:
            d = safe_float(s.get("d"), 0.0)
            lam = safe_float(s.get("lambda") or s.get("lam"), 0.0)
            mu = safe_float(s.get("mu"), 0.0)
            if d <= 0 or lam <= 0:
                errors.append(f"{name}: Dicke d und λ müssen > 0 sein.")
                continue
            R = d / lam
            sd = mu * d
            schicht_out.append({"name": name, "d": d, "lambda": lam, "mu": mu,
                                "r": round(R, 3), "sd": round(sd, 3), "luftschicht": False})
        R_layers.append(R)
        sd_layers.append(sd)
    if errors:
        return {"ok": False, "errors": errors}

    R_total = GLASER_R_SI + sum(R_layers) + GLASER_R_SE
    U = 1.0 / R_total
    q = U * (TAU_THETA_I - TAU_THETA_E)   # Wärmestromdichte Tauperiode

    # --- Temperaturen + Sättigungsdampfdruck an den Schichtgrenzen ----------
    # Knoten 0 = Innenoberfläche, Knoten n = Außenoberfläche.
    n = len(R_layers)
    theta_nodes: List[float] = []
    theta_si = TAU_THETA_I - q * GLASER_R_SI
    theta_nodes.append(theta_si)
    # f_Rsi-Nachweis (DIN 4108-2 §6.2): gleiche Randbedingungen wie Tauperiode.
    f_rsi = (theta_si - TAU_THETA_E) / (TAU_THETA_I - TAU_THETA_E)
    f_rsi_erfuellt = f_rsi >= F_RSI_MIN
    acc = GLASER_R_SI
    for k in range(n):
        acc += R_layers[k]
        theta_nodes.append(TAU_THETA_I - q * acc)
    # theta_nodes[n] == theta_se

    sd_nodes = [0.0]
    for k in range(n):
        sd_nodes.append(sd_nodes[-1] + sd_layers[k])
    sd_total = sd_nodes[-1]

    psat_nodes = [p_sat(t) for t in theta_nodes]

    # --- Tauperiode: untere konvexe Hülle = Dampfdruckverlauf --------------
    # Stützpunkte: innen (p_i) ... Sättigung an inneren Grenzen ... außen (p_e).
    pts: List[Tuple[float, float]] = [(0.0, TAU_P_I)]
    for k in range(1, n):
        pts.append((sd_nodes[k], psat_nodes[k]))
    pts.append((sd_total, TAU_P_E))
    hull = _lower_convex_hull(pts)

    # tatsächlicher Dampfdruck an jedem Knoten = Hüllen-Interpolation
    def hull_p(sd: float) -> float:
        for a, b in zip(hull, hull[1:]):
            xa, ya = pts[a]
            xb, yb = pts[b]
            if xa - 1e-12 <= sd <= xb + 1e-12:
                if xb - xa < 1e-12:
                    return ya
                return ya + (yb - ya) * (sd - xa) / (xb - xa)
        return pts[hull[-1]][1]

    # Kondensationsebenen = innere Hüllenknoten, die auf der Sättigung liegen
    tauebenen: List[Dict[str, Any]] = []
    for idx in hull:
        if idx == 0 or idx == len(pts) - 1:
            continue
        sd_c = pts[idx][0]
        pc = pts[idx][1]   # = psat dort (Hüllenknoten an Sättigung)
        tauebenen.append({"node": idx, "sd_c": sd_c, "pc": pc,
                          "grenze_nach": schicht_out[idx - 1]["name"] if idx - 1 < len(schicht_out) else ""})

    # --- Tauwassermasse je Ebene: g_in − g_out (verallgemeinert A.3–A.11) ---
    mc_total = 0.0
    for t in range(len(tauebenen)):
        sd_c = tauebenen[t]["sd_c"]
        pc = tauebenen[t]["pc"]
        sd_prev = tauebenen[t - 1]["sd_c"] if t > 0 else 0.0
        p_prev = tauebenen[t - 1]["pc"] if t > 0 else TAU_P_I
        sd_next = tauebenen[t + 1]["sd_c"] if t + 1 < len(tauebenen) else sd_total
        p_next = tauebenen[t + 1]["pc"] if t + 1 < len(tauebenen) else TAU_P_E
        g_in = DELTA_0 * (p_prev - pc) / (sd_c - sd_prev) if sd_c - sd_prev > 0 else 0.0
        g_out = DELTA_0 * (pc - p_next) / (sd_next - sd_c) if sd_next - sd_c > 0 else 0.0
        gc = g_in - g_out
        mc = max(gc, 0.0) * T_PERIODE_S
        tauebenen[t]["mc"] = round(mc, 4)
        mc_total += mc

    # --- Verdunstungsperiode: Tauebenen auf p_sat,Verd, Abgabe zu beiden Seiten
    mev_total = 0.0
    for t in range(len(tauebenen)):
        sd_c = tauebenen[t]["sd_c"]
        # nach innen bis zur vorigen Tauebene (bzw. Innenoberfläche), nach außen analog
        sd_prev = tauebenen[t - 1]["sd_c"] if t > 0 else 0.0
        sd_next = tauebenen[t + 1]["sd_c"] if t + 1 < len(tauebenen) else sd_total
        # zwischen zwei Tauebenen kein Strom (gleicher p_sat,Verd) → halber Abstand entfällt;
        # vereinfachend Abgabe zur jeweils näheren Oberfläche (A.14/A.15).
        sd_innen = sd_c - (sd_prev if t > 0 else 0.0)
        sd_aussen = (sd_next if t + 1 < len(tauebenen) else sd_total) - sd_c
        g_innen = DELTA_0 * (verd_psat - VERD_P_I) / sd_innen if sd_innen > 0 else 0.0
        g_aussen = DELTA_0 * (verd_psat - VERD_P_E) / sd_aussen if sd_aussen > 0 else 0.0
        mev = (g_innen + g_aussen) * T_PERIODE_S
        tauebenen[t]["mev"] = round(mev, 4)
        mev_total += mev

    tauwasser = mc_total > 1e-6
    # Bewertung §5.2.2: M_c ≤ M_ev und M_c ≤ 1,0 kg/m²; zusätzlich f_Rsi ≥ 0,70
    glaser_erfuellt = (not tauwasser) or (mc_total <= mev_total + 1e-9 and mc_total <= MC_MAX_ALLG + 1e-9)
    erfuellt = glaser_erfuellt and f_rsi_erfuellt

    # Knotenprofil für die Anzeige (Diffusionsdiagramm)
    profil = []
    for k in range(n + 1):
        profil.append({
            "node": k,
            "position": schicht_out[k - 1]["name"] if k > 0 else "Innenoberfläche",
            "sd": round(sd_nodes[k], 3),
            "theta": round(theta_nodes[k], 2),
            "p_sat": round(psat_nodes[k], 0),
            "p": round(hull_p(sd_nodes[k]), 0),
        })

    if not tauwasser:
        msg = "Kein Tauwasserausfall im Bauteilquerschnitt → diffusionstechnisch zulässig."
    elif glaser_erfuellt:
        msg = (f"Tauwasser {mc_total:.3f} kg/m² fällt an, verdunstet aber wieder "
               f"({mev_total:.3f} kg/m²) und bleibt unter 1,0 kg/m² → zulässig.")
    else:
        grund = []
        if mc_total > mev_total:
            grund.append("Verdunstung reicht nicht (M_c > M_ev)")
        if mc_total > MC_MAX_ALLG:
            grund.append("M_c > 1,0 kg/m²")
        msg = f"Tauwasser {mc_total:.3f} kg/m² – {', '.join(grund)} → nicht zulässig."
    if not f_rsi_erfuellt:
        msg += (f" Zusätzlich f_Rsi = {f_rsi:.2f} < 0,70 → Schimmel-/Tauwassergefahr "
                "an der Innenoberfläche (DIN 4108-2 §6).")

    return {
        "ok": True,
        "calculation_basis": "DIN 4108-3:2024-03, Anhang A – Periodenbilanzverfahren (Glaser)",
        "bauteil_typ": bauteil_typ,
        "schichten": schicht_out,
        "u_wert": round(U, 3),
        "r_total": round(R_total, 3),
        "sd_total": round(sd_total, 3),
        "theta_si": round(theta_si, 2),
        "f_rsi": round(f_rsi, 3),
        "f_rsi_min": F_RSI_MIN,
        "f_rsi_erfuellt": f_rsi_erfuellt,
        "profil": profil,
        "tauwasser": tauwasser,
        "tauebenen": tauebenen,
        "mc_total": round(mc_total, 4),
        "mev_total": round(mev_total, 4),
        "mc_max_zulaessig": MC_MAX_ALLG,
        "erfuellt": erfuellt,
        "rating_label": "Erfüllt" if erfuellt else "Nicht erfüllt",
        "rating_color": "green" if erfuellt else "red",
        "rating_message": msg,
    }


# ===========================================================================
# FEATURE 4 — Wärmebrücken (Beiblatt 2) + Luftdichtheit n50 (Teil 7)
# ===========================================================================
# Wärmebrückenzuschlag ΔU_WB (DIN V 18599-2 i.V.m. DIN 4108 Bbl 2:2019-06, §5.2).
DELTA_U_WB_OPTIONEN = {
    "keine":      {"wert": 0.10, "label": "Kein Nachweis (Pauschalwert ΔU_WB = 0,10)"},
    "innen":      {"wert": 0.15, "label": "Innendämmung + einbindende Massivdecke (0,15)"},
    "kat_a":      {"wert": 0.05, "label": "Anschlüsse nach DIN 4108 Bbl 2 – Kategorie A (0,05)"},
    "kat_b":      {"wert": 0.03, "label": "Anschlüsse nach DIN 4108 Bbl 2 – Kategorie B (0,03)"},
}
# Luftdichtheit – Grenzwerte n50 (DIN 4108-7:2026-04, §5; deckungsgleich GEG 2024).
N50_GRENZ_OHNE_RLT = 3.0   # h⁻¹, ohne raumlufttechnische Anlage
N50_GRENZ_MIT_RLT = 1.5    # h⁻¹, mit RLT-Anlage (Empfehlung ≤ 1,0)
QE50_GRENZ_OHNE_RLT = 4.5  # m³/(h·m²), Gebäude > 1500 m³
QE50_GRENZ_MIT_RLT = 2.0


def waermebruecken_zuschlag(option: str) -> Dict[str, Any]:
    """ΔU_WB-Wert + Beschreibung zu einer gewählten Nachweis-Kategorie."""
    info = DELTA_U_WB_OPTIONEN.get(option, DELTA_U_WB_OPTIONEN["keine"])
    return {"option": option if option in DELTA_U_WB_OPTIONEN else "keine",
            "delta_u_wb": info["wert"], "label": info["label"]}


def pruefe_luftdichtheit(data: Dict[str, Any]) -> Dict[str, Any]:
    """n50-/q_E50-Nachweis nach DIN 4108-7:2026-04, §5.

    data: n50 [h⁻¹] (gemessen), mit_rlt (bool), volumen [m³] (optional),
          qe50 [m³/(h·m²)] (optional, für V > 1500 m³).
    """
    n50 = safe_float(data.get("n50"), 0.0)
    mit_rlt = bool(data.get("mit_rlt"))
    volumen = safe_float(data.get("volumen"), 0.0)
    n50_grenz = N50_GRENZ_MIT_RLT if mit_rlt else N50_GRENZ_OHNE_RLT
    n50_ok = n50 <= n50_grenz + 1e-9 if n50 > 0 else None

    out: Dict[str, Any] = {
        "ok": True,
        "calculation_basis": "DIN 4108-7:2026-04, §5 (Luftdichtheit, n50 nach DIN EN ISO 9972 Verfahren 3)",
        "n50": round(n50, 2) if n50 > 0 else None,
        "n50_grenze": n50_grenz,
        "mit_rlt": mit_rlt,
        "n50_erfuellt": n50_ok,
        "empfehlung_rlt": N50_GRENZ_MIT_RLT if mit_rlt else None,
    }
    # Infiltrations-Luftwechsel (informativ): n_inf ≈ n50 · e (windschwach, einseitig e≈0,07)
    if n50 > 0:
        e_faktor = safe_float(data.get("e_faktor"), 0.07) or 0.07
        out["n_infiltration"] = round(n50 * e_faktor, 3)
        out["e_faktor"] = e_faktor

    if volumen > 1500:
        qe50 = safe_float(data.get("qe50"), 0.0)
        qe50_grenz = QE50_GRENZ_MIT_RLT if mit_rlt else QE50_GRENZ_OHNE_RLT
        out["qe50"] = round(qe50, 2) if qe50 > 0 else None
        out["qe50_grenze"] = qe50_grenz
        out["qe50_erfuellt"] = (qe50 <= qe50_grenz + 1e-9) if qe50 > 0 else None

    if n50_ok is None:
        out["rating_label"] = "—"
        out["rating_color"] = "yellow"
        out["rating_message"] = "Kein n50-Messwert angegeben. Grenzwert siehe oben."
    elif n50_ok:
        out["rating_label"] = "Erfüllt"
        out["rating_color"] = "green"
        out["rating_message"] = f"n50 = {n50:.2f} h⁻¹ ≤ {n50_grenz} h⁻¹ → luftdicht nach DIN 4108-7."
    else:
        out["rating_label"] = "Nicht erfüllt"
        out["rating_color"] = "red"
        out["rating_message"] = f"n50 = {n50:.2f} h⁻¹ > {n50_grenz} h⁻¹ → Anforderung nicht erfüllt."
    return out
