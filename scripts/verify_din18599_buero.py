#!/usr/bin/env python
"""Verifikation des DIN-V-18599-2-Monatsbilanz-Kerns an einem Referenz-Bürogebäude
(Nichtwohngebäude, Nutzungsprofil "Einzelbüro" nach DIN V 18599-10).

Ergänzt scripts/verify_din18599.py (dort: Wohngebäude/EFH) um ein Nichtwohngebäude-Beispiel,
damit auch die Nichtwohn-Zweige (Nutzungsprofilauflösung building_type/-variant → PROFILES,
siehe resolve_profile()) an einem konkreten Fall überprüft sind.

Referenzgebäude (frei gewählt, nachvollziehbar):
  Bürogebäude, Nichtwohngebäude, Nutzung "Einzelbüro", 300 m² BGF, Raumhöhe 3,0 m.
  Fassaden je Orientierung 40 m² brutto (160 m² gesamt), U = 0,28 W/m²K.
  Dach 150 m², U = 0,22 ; Bodenplatte 150 m², U·F_x = 0,30·0,5 = 0,15.
  Fenster gesamt 46 m² (N10/O8/S20/W8), U = 1,10 ; g = 0,50. Kein separates Türelement.
  Wärmebrücken ΔU_WB = 0,10 · Σ(A_i·F_x) über Wand-BRUTTO (=netto+Fenster+Tür) + Dach + Boden,
  also A_Hülle = 160 (Wand brutto, inkl. Fenster) + 150 (Dach) + 150 (Boden) = 460 m² (+46,0 W/K)
  – die Fensterfläche zählt nur einmal (steckt schon in den 160 m² Wand-brutto), siehe
  din18599.py calculate_heat_demand(): wb_area summiert wall_net + windows + doors je
  Orientierung, das ergibt wieder die Bruttofläche.
  Bauweise mittel (c_wirk = 90 Wh/m²K).

  Handrechnung H_T (Wände netto 160 - 46 = 114 m²):
    H_T = 114*0,28 + 150*0,22 + 150*0,15 + 46*1,10 + 46,0
        =  31,92  +  33,00  +  22,50  +  50,60  +  46,0  = 184,02 W/K
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geglca.settings")
import django
django.setup()

from dashboard.services.din18599 import calculate_heat_demand, resolve_profile, PROFILES

BUERO = {
    "bgf": 300, "room_height": 3.0,
    "building_type": "nichtwohngebaeude", "building_type_variant": "Bürogebäude",
    "north_area": 40, "north_u": 0.28,
    "south_area": 40, "south_u": 0.28,
    "east_area": 40, "east_u": 0.28,
    "west_area": 40, "west_u": 0.28,
    "roof_area": 150, "roof_u": 0.22,
    "floor_area": 150, "floor_u": 0.15,   # 0,30 * F_x 0,5 (erdberührt)
    "window_north_area": 10, "window_south_area": 20,
    "window_east_area": 8, "window_west_area": 8,
    "window_u": 1.10, "g_value": 0.50,
}

HAND_HT = 114 * 0.28 + 150 * 0.22 + 150 * 0.15 + 46 * 1.10 + 46.0


def main():
    ok = True

    # 1) Profilauflösung: "Bürogebäude" (wörtlicher Frontend-String, nicht der interne Key)
    #    muss auf "einzelbuero" mit den Teil-10-Kennwerten auflösen - keine stille Rückstufung
    #    auf das Wohngebäude-EFH-Profil (historischer Bug, siehe din18599.py Kommentar).
    profile_key = resolve_profile("nichtwohngebaeude", "Bürogebäude")
    profile_ok = profile_key == "einzelbuero"
    print(("  ✓ " if profile_ok else "  ✗ ") + f"Profilauflösung 'Bürogebäude' → '{profile_key}' (erwartet 'einzelbuero')")
    ok = ok and profile_ok
    prof = PROFILES["einzelbuero"]
    print(f"    θ_i={prof['theta_i']} °C · q_i={prof['q_i']} Wh/(m²·d) · air_change={prof['air_change']} 1/h "
          f"· usage_days={prof['usage_days']} · usage_hours={prof['usage_hours']}")

    r = calculate_heat_demand(BUERO)
    if not r.get("ok"):
        print("FEHLER:", r.get("errors"))
        sys.exit(1)

    print("=" * 78)
    print("REFERENZ-BÜROGEBÄUDE (Nichtwohngebäude, Einzelbüro)  –  DIN V 18599-2 Monatsbilanz")
    print("=" * 78)
    print(f"H_T (Transmission)        = {r['h_transmission']:>8.2f} W/K   (Handrechnung: {HAND_HT:.2f} W/K)")
    print(f"H_V (Lüftung)             = {r['h_ventilation']:>8.2f} W/K")
    print(f"H gesamt                  = {r['h_total']:>8.2f} W/K")
    print(f"Zeitkonstante tau         = {r['time_constant_h']:>8.1f} h")
    print("-" * 78)
    print(f"HEIZWÄRMEBEDARF     Q_h,b,a    = {r['adjusted_heat_demand_kwh']:>10.1f} kWh/a")
    print(f"spezifisch                     = {r['specific_heat_demand']:>10.2f} kWh/(m²a)")
    print(f"Bewertung                      = {r['rating_label']}")
    print("=" * 78)

    diff_ht = abs(r["h_transmission"] - HAND_HT)
    ht_ok = diff_ht < 0.5
    abw_pct = 100.0 * diff_ht / HAND_HT
    print(("  ✓ " if ht_ok else "  ✗ ") + f"H_T Tool vs. Handrechnung: Abweichung {diff_ht:.2f} W/K ({abw_pct:.2f} %)")
    ok = ok and ht_ok

    spec = r["specific_heat_demand"]
    plausibel = 20 <= spec <= 150
    print(("  ✓ " if plausibel else "  ✗ ") + f"Plausibilität (20–150 kWh/m²a für Bürogebäude): {spec}")
    ok = ok and plausibel

    print("\nALLE TESTS BESTANDEN ✅" if ok else "\nFEHLER ❌")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
