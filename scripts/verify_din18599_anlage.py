#!/usr/bin/env python
"""Verifikation Stufe 2: Anlagentechnik nach DIN V 18599-5/-6/-8 am Referenz-EFH.

Gleiche Hülle wie scripts/verify_din18599.py; getestet werden alle vier
Erzeugervarianten sowie der WRG-Effekt der Lüftungsanlage.
"""
import os
import sys
import django

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geglca.settings")
django.setup()

from dashboard.services.din18599_anlage import calculate_system_din

ENVELOPE = {
    "bgf": 150, "room_height": 2.6, "building_type": "wohngebaeude",
    "building_type_variant": "EFH",
    "north_area": 30, "north_u": 0.24, "south_area": 30, "south_u": 0.24,
    "east_area": 30, "east_u": 0.24, "west_area": 30, "west_u": 0.24,
    "roof_area": 100, "roof_u": 0.20, "floor_area": 100, "floor_u": 0.175,
    "window_north_area": 5, "window_south_area": 15,
    "window_east_area": 5, "window_west_area": 5,
    "window_u": 1.10, "g_value": 0.60,
    "door_south_count": 1, "door_area_per_unit": 2.0, "door_u": 1.30,
}


def run(name, payload):
    r = calculate_system_din(payload)
    if not r.get("ok"):
        print(f"{name}: FEHLER {r.get('errors')}")
        return None
    d = r["din"]
    print(f"--- {name} ---")
    print(f"  Q_h,b={d['q_h_b']:.0f}  Q_h,ce={d['q_h_ce']:.0f}  Q_h,d={d['q_h_d']:.0f}"
          f"  Q_h,s={d['q_h_s']:.0f}  → Q_h,outg={d['q_h_outg']:.0f} kWh/a"
          f"  (+Erz.verlust {d['q_h_gen_loss']:.0f})")
    print(f"  Q_w,b={d['q_w_b']:.0f}  Q_w,d={d['q_w_d']:.0f}  Q_w,s={d['q_w_s']:.0f}"
          f"  → Q_w,outg={d['q_w_outg']:.0f} kWh/a  (+Erz.verlust {d['q_w_gen_loss']:.0f})")
    if d['district_station_loss']:
        print(f"  Fernwärme-Stationsverlust: {d['district_station_loss']:.0f} kWh/a")
    print(f"  Hilfsenergie: Pumpe {d['aux_pump_heating']:.0f} + Kessel {d['aux_boiler']:.0f}"
          f" + Zirk. {d['aux_circulation_pump']:.0f} + Ventilator {d['aux_fans']:.0f}"
          f" = {r['auxiliary_electricity']:.0f} kWh/a")
    if d.get("jaz"):
        print(f"  Jahresarbeitszahl (JAZ): {d['jaz']}")
    print(f"  Endenergie: Heizung {r['heating_end_energy']:.0f} + TWW {r['hotwater_end_energy']:.0f}"
          f" + Hilfsstrom {r['auxiliary_electricity']:.0f} = {r['total_end_energy']:.0f} kWh/a")
    print(f"  Primärenergie: {r['primary_energy']:.0f} kWh/a"
          f" ({r['specific_primary_energy']:.1f} kWh/m²a, {r['system_label']})"
          f"   CO₂: {r['co2_emissions']:.0f} kg/a")
    print(f"  n_eff = {d['n_eff_air_change']}  |  Leitungen H: {d['pipe_lengths_heating_m']}"
          f"  TWW: {d['pipe_lengths_dhw_m']}  |  Speicher {d['dhw_storage_liters']:.0f} l"
          f"  |  P_n = {d['p_n_kw']} kW (Φ_max {d['phi_max_kw']} kW)")
    return r


def main():
    base = {"bgf": 150, "room_height": 2.6, "building_type": "wohngebaeude",
            "building_type_variant": "EFH", "envelope": ENVELOPE,
            "ventilation_system_type": "none"}

    print("=" * 86)
    print("REFERENZ-EFH (150 m²) – Anlagentechnik DIN V 18599-5/-6/-8")
    print("=" * 86)

    gas = run("Gas-Brennwert + Heizkörper 55/45", {**base, "heating_system": "gas"})
    run("Pelletkessel + Heizkörper 55/45", {**base, "heating_system": "pellet"})
    run("Fernwärme + Heizkörper 55/45", {**base, "heating_system": "district"})
    wp = run("Wärmepumpe (COP 3,5 @A2/W35) + FBH 35/28", {**base, "heating_system": "heatpump", "cop": 3.5})
    wrg = run("Wärmepumpe + Lüftung mit WRG 80 % (DC)",
              {**base, "heating_system": "heatpump", "cop": 3.5,
               "ventilation_system_type": "balanced_hr",
               "ventilation_heat_recovery_eff": 0.8, "ventilation_fan_type": "dc"})

    print("=" * 86)
    print("Plausibilität:")
    if gas:
        e = gas["total_end_energy"] / 150
        print(f"  Gas Endenergie spezifisch: {e:.1f} kWh/m²a  (erwartet ~80–110) "
              f"{'OK' if 60 <= e <= 130 else 'PRÜFEN'}")
    if wp:
        jaz = wp["din"]["jaz"]
        print(f"  WP JAZ: {jaz}  (erwartet 3,0–4,5 bei FBH) "
              f"{'OK' if 2.8 <= jaz <= 4.8 else 'PRÜFEN'}")
    if wp and wrg:
        diff = wp["adjusted_heat_demand_net"] - wrg["adjusted_heat_demand_net"]
        print(f"  WRG senkt Heizwärmebedarf um {diff:.0f} kWh/a "
              f"{'OK' if diff > 500 else 'PRÜFEN'}")


if __name__ == "__main__":
    main()
