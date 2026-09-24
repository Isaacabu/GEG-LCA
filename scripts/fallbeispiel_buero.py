#!/usr/bin/env python
"""Referenz-Fallbeispiel Buerogebaeude (Nichtwohngebaeude, Einzelbuero-Nutzungsprofil):
rechnet Huelle + Anlagentechnik + Wand-GWP ueber dieselben Funktionen wie die Live-App
(calculate_heat_demand, calculate_system_din) und gibt das Ergebnis als JSON aus.
Geometrie ist an das im Tool gespeicherte Beispielprojekt "Fallbeispiel Buero" angeglichen
(siehe Kommentare unten). Aufruf: python scripts/fallbeispiel_buero.py"""
import os
import sys
import json
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geglca.settings")
import django
django.setup()

from dashboard.services.din18599 import calculate_heat_demand
from dashboard.services.din18599_anlage import calculate_system_din
from dashboard.models import EkobaudatMaterial

# --- Geometrie / Bauteile -----------------------------------------------
# WICHTIG: Diese Werte sind NICHT mehr die urspruenglichen Vorgaben aus der Aufgabenstellung
# (BGF 2.800/NGF 2.400/Wand 1.150 m²), sondern die TATSAECHLICHE Geometrie, die im laufenden
# Tool ueber die UI eingegeben und als Projekt "Fallbeispiel Buero" gespeichert wurde (Grundriss
# 24,5 x 24,5 m, 4 Geschosse a 3,2 m). Grund: das Tool hat nur EIN Flaechenfeld (bgf), aus dem
# BGF/NGF und alle vier Fassadenflaechen gemeinsam ueber Laenge x Breite x Geschosse abgeleitet
# werden - BGF=2.400 m² UND 382,5 m² Fassade je Seite gleichzeitig zu treffen ist mit diesem
# Modell rechnerisch unmoeglich (siehe abweichungen.md Punkt 1, aktualisiert). Diese Datei
# bildet jetzt exakt das ab, was in abb20_neu.png/abb21_neu.png zu sehen ist.
NGF = 2401.0   # = BGF; das Tool kennt nur ein Flaechenfeld, siehe oben

WALL_AREA_OPAK_TOTAL = 874.4   # 4 x 218,6 m² (Bruttofassade 313,6 - Fenster 95 je Seite)
WINDOW_AREA_TOTAL = 380.0
ROOF_AREA = 630.0
FLOOR_AREA = 600.3    # vom Tool aus dem Grundriss abgeleitet, nicht frei editierbar

WALL_AREA_GROSS_PER_ORI = 313.6   # Laenge/Breite (24,5 m) x Gesamthoehe (4 x 3,2 m)
WINDOW_AREA_PER_ORI = WINDOW_AREA_TOTAL / 4

# U-Wert Aussenwand: Stahlbeton 200mm (lambda=2.30) + Mineralwolle 180mm (lambda=0.035),
# hinterlueftete Bekleidungsebene (Luftschicht+Verkleidung) traegt nach DIN 4108-4/EN ISO 6946
# konventionell keinen R-Wert bei -> Rsi 0,13 + Rse 0,04 (Standard des Tools).
R_SI, R_SE = 0.13, 0.04
R_BETON = 0.200 / 2.30
R_MW = 0.180 / 0.035
U_WALL = round(1.0 / (R_SI + R_BETON + R_MW + R_SE), 3)

U_ROOF = 0.16
U_WINDOW = 1.10

# Bodenplatte gegen Erdreich: F_x nach DIN V 18599-2 Tab. 6 (erdberuehrt, R-/B'-abhaengig,
# 0,30-0,55) - hier 0,40 als plausibler Mittelwert fuer ein groesseres Gebaeude angesetzt
# (keine Perimeter-/B'-Angabe im Fallbeispiel vorgegeben -> dokumentierte Annahme).
U_FLOOR_RAW = 0.28
FX_FLOOR = 0.40
U_FLOOR_EFF = round(U_FLOOR_RAW * FX_FLOOR, 4)

BUERO = {
    "bgf": NGF, "room_height": 3.2,
    "building_type": "nichtwohngebaeude", "building_type_variant": "Bürogebäude",
    "north_area": WALL_AREA_GROSS_PER_ORI, "north_u": U_WALL,
    "south_area": WALL_AREA_GROSS_PER_ORI, "south_u": U_WALL,
    "east_area": WALL_AREA_GROSS_PER_ORI, "east_u": U_WALL,
    "west_area": WALL_AREA_GROSS_PER_ORI, "west_u": U_WALL,
    "roof_area": ROOF_AREA, "roof_u": U_ROOF,
    "floor_area": FLOOR_AREA, "floor_u": U_FLOOR_EFF,
    "window_north_area": WINDOW_AREA_PER_ORI, "window_south_area": WINDOW_AREA_PER_ORI,
    "window_east_area": WINDOW_AREA_PER_ORI, "window_west_area": WINDOW_AREA_PER_ORI,
    "window_u": U_WINDOW, "g_value": 0.55,  # Tool-UI-Default fuer Fenster (abgeglichen mit abb20_neu.png)
}


def eff_class(spec_endenergie):
    bands = [("A+", 30), ("A", 50), ("B", 75), ("C", 100), ("D", 130),
             ("E", 160), ("F", 200), ("G", 250), ("H", float("inf"))]
    for label, mx in bands:
        if spec_endenergie < mx:
            return label
    return "H"


def wand_gwp():
    """Graue Emissionen A1-A3 der Aussenwand (Stahlbeton + Mineralwolle), 1:1 die Formel aus
    EkobaudatMaterialViewSet.wall_gwp (views.py)."""
    LAYER_OBD_MAP = {
        "stahlbeton": "8347f9a7-f4ec-4a36-a266-a0281f5fd16d",
        "mw": "699e3d57-72b4-402d-a0ee-cebb06f3cdf1",
    }
    layers = [("stahlbeton", 200.0, 2300.0), ("mw", 180.0, 45.0)]  # (key, dicke_mm, rohdichte_kg/m3 (Doku))
    rows = []
    total_per_m2 = 0.0
    for key, dicke_mm, _dichte_doc in layers:
        mat = EkobaudatMaterial.objects.filter(uuid=LAYER_OBD_MAP[key]).first()
        thickness_m = dicke_mm / 1000.0
        qty = mat.ref_quantity or 1.0
        unit = (mat.ref_unit or "").lower()
        gwp_per_m2 = None
        if unit == "m3":
            gwp_per_m2 = (mat.gwp_a1a3 / qty) * thickness_m
        elif unit == "kg" and mat.density:
            gwp_per_m2 = (mat.gwp_a1a3 / qty) * mat.density * thickness_m
        rows.append({
            "layer": key, "name": mat.name, "uuid": mat.uuid,
            "dicke_mm": dicke_mm, "rohdichte_kg_m3": mat.density,
            "gwp_a1a3_referenz": mat.gwp_a1a3, "ref_unit": mat.ref_unit, "ref_quantity": qty,
            "gwp_per_m2": round(gwp_per_m2, 3) if gwp_per_m2 is not None else None,
        })
        total_per_m2 += gwp_per_m2 or 0.0
    return rows, round(total_per_m2, 3)


def main():
    r = calculate_heat_demand(BUERO)
    if not r.get("ok"):
        print("FEHLER Heizwaerme:", r.get("errors"))
        sys.exit(1)

    # calculate_system_din liest die Huellendaten NICHT flach, sondern unter dem Schluessel
    # "envelope" (so schickt es auch das Frontend, siehe CLAUDE.md: "sendet das letzte
    # Envelope-Payload mit") und rechnet die Teil-2-Bilanz mit dem effektiven Luftwechsel der
    # Anlage neu (din18599_anlage.py:277-295). Ohne "envelope" faellt es still auf
    # heat_demand_net=0 zurueck - das haette hier sonst q_h_b=0 ergeben.
    sys_full = dict(BUERO)
    sys_full["heating_system"] = "heatpump"
    sys_full["envelope"] = dict(BUERO)
    s = calculate_system_din(sys_full)
    if not s.get("ok"):
        print("FEHLER Anlage:", s.get("errors"))
        sys.exit(1)

    wand_rows, wand_gwp_total = wand_gwp()
    wand_flaeche_gesamt = WALL_AREA_OPAK_TOTAL

    out = {
        "input": BUERO,
        "u_wert_wand_berechnung": {
            "R_si": R_SI, "R_beton_200mm": round(R_BETON, 4), "R_mw_180mm": round(R_MW, 4),
            "R_se": R_SE, "U_wand": U_WALL,
        },
        "u_wert_boden": {"U_roh": U_FLOOR_RAW, "F_x": FX_FLOOR, "U_eff": U_FLOOR_EFF},
        "heizwaerme": r,
        "anlage": s,
        "effizienzklasse_endenergie": eff_class(s.get("specific_end_energy", 0.0)),
        "wand_gwp_layers": wand_rows,
        "wand_gwp_per_m2": wand_gwp_total,
        "wand_gwp_gesamt_kg": round(wand_gwp_total * wand_flaeche_gesamt, 1),
        "wand_gwp_je_m2_ngf": round(wand_gwp_total * wand_flaeche_gesamt / NGF, 3),
    }
    with open("thesis_export/_fallbeispiel_raw.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
