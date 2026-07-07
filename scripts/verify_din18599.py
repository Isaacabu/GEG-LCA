#!/usr/bin/env python
"""Verifikation des DIN-V-18599-2-Monatsbilanz-Kerns an einem Referenz-EFH.

Referenzgebäude (frei gewählt, nachvollziehbar):
  Einfamilienhaus, 150 m² beheizte Fläche, kompakter Baukörper, GEG-naher Dämmstandard.
  Hüllflächen (effektive U-Werte inkl. F_x); Fassaden BRUTTO – Fenster/Türen werden
  im Rechenkern abgezogen (wie bei der Geometrie-Eingabe der Website):
    Fassaden gesamt 120 m² (je Orientierung 30 m² brutto), U = 0,24 W/m²K
    Dach 100 m², U = 0,20 ; Bodenplatte 100 m², U·F_x = 0,35·0,5 = 0,175
    Fenster gesamt 30 m² (N5/O5/S15/W5), U = 1,10 ; g = 0,60 ; Haustür 2 m², U = 1,30
    → Wände netto 88 m²; Wärmebrücken ΔU_WB = 0,10 auf A_Hülle = 320 m² (+32,0 W/K)
  Bauweise mittel (c_wirk = 90 Wh/m²K), Luftwechsel n = 0,5 /h, θ_i = 20 °C.
  Handrechnung: H_T = 88·0,24 + 100·0,20 + 100·0,175 + 30·1,10 + 2·1,30 + 32,0 = 126,22 W/K
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geglca.settings")
django.setup()

from dashboard.services.din18599 import calculate_heat_demand

EFH = {
    "bgf": 150, "room_height": 2.6, "building_type": "wohngebaeude",
    "building_type_variant": "EFH",
    "north_area": 30, "north_u": 0.24,
    "south_area": 30, "south_u": 0.24,
    "east_area": 30, "east_u": 0.24,
    "west_area": 30, "west_u": 0.24,
    "roof_area": 100, "roof_u": 0.20,
    "floor_area": 100, "floor_u": 0.175,   # 0,35 * F_x 0,5 (erdberührt)
    "window_north_area": 5, "window_south_area": 15,
    "window_east_area": 5, "window_west_area": 5,
    "window_u": 1.10, "g_value": 0.60,
    "door_south_count": 1, "door_area_per_unit": 2.0, "door_u": 1.30,
}


def main():
    r = calculate_heat_demand(EFH)
    if not r.get("ok"):
        print("FEHLER:", r.get("errors"))
        return

    print("=" * 78)
    print("REFERENZ-EFH  –  DIN V 18599-2 Monatsbilanz")
    print("=" * 78)
    print(f"H_T (Transmission)        = {r['h_transmission']:>8.2f} W/K")
    print(f"H_V (Lüftung)             = {r['h_ventilation']:>8.2f} W/K")
    print(f"H gesamt                  = {r['h_total']:>8.2f} W/K")
    print(f"Zeitkonstante tau         = {r['time_constant_h']:>8.1f} h")
    print("-" * 78)
    print(f"{'Monat':5} {'θe':>6} {'Q_sink':>9} {'Q_sol':>8} {'Q_int':>8} {'γ':>7} {'η':>7} {'Q_heiz':>9}")
    for m in r["monthly"]:
        print(f"{m['month']:5} {m['theta_e']:>6.1f} {m['q_sink']:>9.1f} {m['q_solar']:>8.1f} "
              f"{m['q_internal']:>8.1f} {m['gamma']:>7.3f} {m['eta']:>7.3f} {m['q_heat']:>9.1f}")
    print("-" * 78)
    print(f"Brutto-Wärmesenken  Q_sink,a   = {r['annual_heat_demand_kwh']:>10.1f} kWh/a")
    print(f"Solare Gewinne      Q_S,a      = {r['solar_gain_kwh']:>10.1f} kWh/a")
    print(f"Interne Gewinne     Q_I,a      = {r['internal_gain_kwh']:>10.1f} kWh/a")
    print(f"HEIZWÄRMEBEDARF     Q_h,b,a    = {r['adjusted_heat_demand_kwh']:>10.1f} kWh/a")
    print(f"spezifisch                     = {r['specific_heat_demand']:>10.2f} kWh/(m²a)")
    print(f"Bewertung                      = {r['rating_label']}")
    print("=" * 78)

    # --- Plausibilitätsprüfung ---
    spec = r["specific_heat_demand"]
    ok = 20 <= spec <= 100
    print(f"Plausibilität (20–100 kWh/m²a für EFH GEG-nah): {'OK' if ok else 'AUSSERHALB'} ({spec})")


if __name__ == "__main__":
    main()
