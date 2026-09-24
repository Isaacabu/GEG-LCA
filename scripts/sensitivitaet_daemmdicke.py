#!/usr/bin/env python
"""Sensitivitaetsanalyse Daemmdicke Aussenwand (Mineralwolle) 0-500mm, Schrittweite 20mm,
fuer das Referenz-Fallbeispiel Buerogebaeude (siehe fallbeispiel_buero.py, identische
Wandflaechen/Geometrie). Je Schritt: U-Wert, H_T, Q_h,b, Endenergie, Betriebs-CO2 ueber
50 Jahre (zwei Strommix-Szenarien) und graue Emissionen A1-A3 der Daemmschicht.
Aufruf: python scripts/sensitivitaet_daemmdicke.py"""
import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geglca.settings")
import django
django.setup()

from dashboard.services.din18599 import calculate_heat_demand
from dashboard.services.din18599_anlage import calculate_system_din
from dashboard.models import EkobaudatMaterial

# Geometrie abgeglichen mit dem real gespeicherten Tool-Projekt "Fallbeispiel Buero"
# (Grundriss 24,5 x 24,5 m, 4 Geschosse) - siehe scripts/_fallbeispiel_buero.py und
# thesis_export/abweichungen.md Punkt 1 zur Begruendung (BGF+Fassadenflaeche nicht unabhaengig
# einstellbar, nur ein Flaechenfeld im Tool).
NGF = 2401.0
ROOF_AREA = 630.0
FLOOR_AREA = 600.3
WALL_AREA_GROSS_PER_ORI = 313.6
WINDOW_AREA_PER_ORI = 380.0 / 4

R_SI, R_SE = 0.13, 0.04
LAMBDA_BETON = 2.30
LAMBDA_MW = 0.035
R_BETON = 0.200 / LAMBDA_BETON
U_ROOF, U_WINDOW = 0.16, 1.10
U_FLOOR_EFF = 0.28 * 0.40

# CO2-Faktoren Strom [kg/kWh]:
#  - "heute": 0,56 (GEG 2024 Anlage 9, so wie das Tool intern rechnet - din18599_anlage.py F_CO2;
#    ein regulatorischer, kein physikalisch gemessener Wert). Zum Vergleich: der real gemessene
#    deutsche Strommix lag 2024/2025 bei 344-363 g CO2/kWh (Umweltbundesamt, Climate Change
#    13/2025, Icha/Lauf) und sinkt seit Jahren kontinuierlich (1990: 764 g/kWh).
#  - "dekarbonisiert" = 0,1 kg/kWh - illustrativer Zwischenwert fuer einen weitgehend
#    dekarbonisierten Strommix (~70% unter dem 2025er Messwert), KEIN Zitat aus einer einzelnen
#    Studie mit exakt dieser Zahl. Richtungssicher konsistent mit dem in Agora Energiewende /
#    Prognos / Consentec, "Klimaneutrales Stromsystem 2035" (2022), beschriebenen Pfad zu einem
#    klimaneutralen deutschen Stromsystem bis 2035 (dort nicht als einzelner Kennwert fuer ein
#    Zwischenjahr ausgewiesen). Explizit als Szenario-Annahme gekennzeichnet, nicht als
#    gemessener oder studien-zitierter Wert.
CO2_FACTOR_HEUTE = 0.56
CO2_FACTOR_DEKARB = 0.1

mat_mw = EkobaudatMaterial.objects.filter(uuid="699e3d57-72b4-402d-a0ee-cebb06f3cdf1").first()
GWP_MW_PER_M3 = mat_mw.gwp_a1a3 / (mat_mw.ref_quantity or 1.0)  # kg CO2e/m3


def wand_u(daemmdicke_mm):
    r_mw = (daemmdicke_mm / 1000.0) / LAMBDA_MW if daemmdicke_mm > 0 else 0.0
    return round(1.0 / (R_SI + R_BETON + r_mw + R_SE), 4)


def compute_row(daemmdicke_mm):
    u_wall = wand_u(daemmdicke_mm)
    base = {
        "bgf": NGF, "room_height": 3.2,
        "building_type": "nichtwohngebaeude", "building_type_variant": "Bürogebäude",
        "north_area": WALL_AREA_GROSS_PER_ORI, "north_u": u_wall,
        "south_area": WALL_AREA_GROSS_PER_ORI, "south_u": u_wall,
        "east_area": WALL_AREA_GROSS_PER_ORI, "east_u": u_wall,
        "west_area": WALL_AREA_GROSS_PER_ORI, "west_u": u_wall,
        "roof_area": ROOF_AREA, "roof_u": U_ROOF,
        "floor_area": FLOOR_AREA, "floor_u": U_FLOOR_EFF,
        "window_north_area": WINDOW_AREA_PER_ORI, "window_south_area": WINDOW_AREA_PER_ORI,
        "window_east_area": WINDOW_AREA_PER_ORI, "window_west_area": WINDOW_AREA_PER_ORI,
        "window_u": U_WINDOW, "g_value": 0.55,
    }
    r = calculate_heat_demand(base)
    if not r.get("ok"):
        return {"daemmdicke_mm": daemmdicke_mm, "u_wert_wand": u_wall, "fehler": ";".join(r.get("errors", []))}

    sys_payload = dict(base)
    sys_payload["heating_system"] = "heatpump"
    sys_payload["envelope"] = dict(base)
    s = calculate_system_din(sys_payload)
    if not s.get("ok"):
        return {"daemmdicke_mm": daemmdicke_mm, "u_wert_wand": u_wall, "fehler": ";".join(s.get("errors", []))}

    end_energy = s["total_end_energy"]  # komplett Strom (Waermepumpe + Beleuchtung), s. Fallbeispiel-Skript
    co2_heute_a = end_energy * CO2_FACTOR_HEUTE
    co2_dekarb_a = end_energy * CO2_FACTOR_DEKARB
    gwp_daemmung_per_m2 = GWP_MW_PER_M3 * (daemmdicke_mm / 1000.0)

    return {
        "daemmdicke_mm": daemmdicke_mm,
        "u_wert_wand_W_m2K": u_wall,
        "h_t_W_K": r["h_transmission"],
        "h_t_strich_W_m2K": r["specific_transmission_loss"],
        "q_hb_spez_kWh_m2a": r["specific_heat_demand"],
        "endenergie_spez_kWh_m2a": s["specific_end_energy"],
        "endenergie_gesamt_kWh_a": end_energy,
        "betriebs_co2_50a_heute_t": round(co2_heute_a * 50 / 1000.0, 2),
        "betriebs_co2_50a_dekarbonisiert_t": round(co2_dekarb_a * 50 / 1000.0, 2),
        "gwp_a1a3_daemmung_kg_je_m2_wand": round(gwp_daemmung_per_m2, 3),
    }


def main():
    rows = [compute_row(d) for d in range(0, 501, 20)]
    fieldnames = list(rows[0].keys())
    with open("thesis_export/sensitivitaet.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
