# -*- coding: utf-8 -*-
"""Plausibilitaets- und Normpruefung: realistisches Neubau-EFH durch alle Stufen."""
import os, sys, django
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geglca.settings")
django.setup()

from dashboard.services.din18599 import calculate_heat_demand
from dashboard.services.din18599_anlage import calculate_system_din, F_PRIMARY, F_CO2, F_HS_HI
import json

def line(): print("-" * 72)

# --- Realistisches Einfamilienhaus (Neubau), Augsburg ---------------------
# Geometrie 10 x 8 m, 2 Vollgeschosse, Raumhoehe 2,6 m
BGF = 160.0
VOL = 10*8*2*2.6   # 416 m3
env = {
    "bgf": BGF, "volume": VOL, "room_height": 2.6,
    "project_state": "Bayern", "elevation_m": 494,
    "building_type": "wohngebaeude", "building_type_variant": "Einfamilienhaus",
    "setpoint_temperature": 20,
    # Waende (Brutto je Orientierung), U 0,20
    "north_area": 52, "north_u": 0.20, "south_area": 52, "south_u": 0.20,
    "east_area": 41.6, "east_u": 0.20, "west_area": 41.6, "west_u": 0.20,
    # Fenster, U 0,95, g 0,50 (3-fach)
    "window_north_area": 4, "window_south_area": 12, "window_east_area": 4.5,
    "window_west_area": 4.5, "window_u": 0.95, "g_value": 0.50,
    # Tuer
    "door_north_count": 1, "door_area_per_unit": 2.0, "door_u": 1.2,
    # Dach U 0,18, Boden U 0,25 mit Erdreich-Fx 0,6
    "roof_area": 80, "roof_u": 0.18, "roof_fx": 1.0,
    "floor_area": 80, "floor_u": 0.25, "floor_fx": 0.6,
}

print("=== STUFE 1: Gebaeudehuelle / Heizwaermebedarf (DIN V 18599-2) ===")
r = calculate_heat_demand(env)
assert r["ok"], r
print(f"BGF {BGF:.0f} m2 | H_T {r['h_transmission']} W/K | H_V {r['h_ventilation']} W/K | H_ges {r['h_total']} W/K")
print(f"Zeitkonstante tau {r['time_constant_h']} h | Luftwechsel {r['air_change_rate']} 1/h")
print(f"Brutto-Waermesenken {r['annual_heat_demand_kwh']} kWh/a")
print(f"Solare Gewinne {r['solar_gain_kwh']} | interne {r['internal_gain_kwh']} kWh/a")
print(f"==> Heizwaermebedarf Q_h,b {r['adjusted_heat_demand_kwh']} kWh/a "
      f"= {r['specific_heat_demand']} kWh/m2a  [{r['rating_label']}]")
print(f"Klima: {r['climate_location_label']} | Hoehe-dT {r['elevation_delta_k']} K | f_rad {r['climate_radiation_factor']}")
line()
print("Monatsgang (theta_e | Senke | Solar | intern | gamma | eta | Q_heiz):")
for m in r["monthly"]:
    print(f"  {m['month']}: {m['theta_e']:5.1f} C | {m['q_sink']:7.0f} | {m['q_solar']:6.0f} | "
          f"{m['q_internal']:6.0f} | g={m['gamma']:.2f} | eta={m['eta']:.2f} | Qh={m['q_heat']:7.0f}")
hb = r["heat_balance"]
comp_sum = sum(hb["transmission"].values()) + hb["ventilation_kwh"]
print(f"heat_balance Check: Komponenten {comp_sum:.1f} vs Senke {hb['sinks_total_kwh']} | "
      f"Q_h,b {hb['heat_demand_kwh']} (erwartet {r['adjusted_heat_demand_kwh']})")
line()

print("\n=== STUFE 2: Anlagentechnik (Teil 5/6/8) – Gas-Brennwert + Heizkoerper ===")
sysreq = dict(env)
sysreq.update({
    "envelope": env, "heat_demand_net": r["adjusted_heat_demand_kwh"],
    "heating_system": "gas", "heat_emission": "radiator", "cop": 3.5,
    "ventilation_system_type": "none", "ventilation_fan_type": "ac",
})
s = calculate_system_din(sysreq)
assert s["ok"], s
din = s["din"]
print(f"Heizlast phi_max {din['phi_max_kw']} kW | Kessel P_n {din['p_n_kw']} kW")
print(f"Q_h,b {din['q_h_b']} -> Uebergabe {din['q_h_ce']} + Verteilung {din['q_h_d']} + "
      f"Speicher {din['q_h_s']} -> Ausg {din['q_h_outg']} | Erzeugerverlust {din['q_h_gen_loss']}")
print(f"TWW: Nutzen {din['q_w_b']} + Vert {din['q_w_d']} + Speicher {din['q_w_s']} -> {din['q_w_outg']} | Erz.verl {din['q_w_gen_loss']}")
print(f"Hilfsstrom: Pumpe {din['aux_pump_heating']} + Kessel {din['aux_boiler']} + Zirk {din['aux_circulation_pump']} + Vent {din['aux_fans']} kWh/a")
print(f"==> Heizung End {s['heating_end_energy']} | TWW End {s['hotwater_end_energy']} | "
      f"Hilfsstrom {s['auxiliary_electricity']} kWh/a")
print(f"==> Endenergie GESAMT {s['total_end_energy']} kWh/a = {s['specific_end_energy']} kWh/m2a")
print(f"==> Primaerenergie {s['primary_energy']} = {s['specific_primary_energy']} kWh/m2a  [{s['system_label']}]")
print(f"==> CO2 {s['co2_emissions']} kg/a = {s['co2_emissions']/BGF:.1f} kg/m2a")
# GEG-Faktor-Gegenrechnung
fuel = s['heating_end_energy'] + s['hotwater_end_energy']
elec = s['auxiliary_electricity']
prim_check = fuel*F_PRIMARY['gas'] + elec*F_PRIMARY['electricity']
co2_check = fuel*F_CO2['gas'] + elec*F_CO2['electricity']
print(f"GEG-Check Primaer: {fuel:.0f}*1,1 + {elec:.0f}*1,8 = {prim_check:.0f} (Tool {s['primary_energy']})")
print(f"GEG-Check CO2:     {fuel:.0f}*0,240 + {elec:.0f}*0,560 = {co2_check:.0f} (Tool {s['co2_emissions']})")
line()

print("\n=== Variante: Luft-Wasser-Waermepumpe + Fussbodenheizung ===")
sysreq2 = dict(sysreq); sysreq2.update({"heating_system": "heatpump", "heat_emission": "floor", "cop": 3.8})
s2 = calculate_system_din(sysreq2)
print(f"JAZ {s2['din']['jaz']} | End(Strom) {s2['total_end_energy']} = {s2['specific_end_energy']} kWh/m2a | "
      f"Primaer {s2['specific_primary_energy']} | CO2 {s2['co2_emissions']/BGF:.1f} kg/m2a [{s2['system_label']}]")
line()

print("\n=== Norm-/GEG-Faktoren im Code ===")
print(f"F_PRIMARY {F_PRIMARY}")
print(f"F_CO2     {F_CO2}")
print(f"Brennwert/Heizwert {F_HS_HI}")
