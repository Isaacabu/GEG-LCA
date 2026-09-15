"""
DIN V 18599 – Mehrzonen-Aggregation (Phase Z2a der Mehrzonen-Vision).

Ruft die UNVERÄNDERTE calculate_heat_demand() je Zone auf und summiert die
Ergebnisse. Bewusste Vereinfachung (analog F_x=0 im Einzonen-Modell): der
Wärmeaustausch über Trennwände zwischen Zonen MIT UNTERSCHIEDLICHER
Solltemperatur wird hier noch nicht berücksichtigt (Phase Z2b, Folgeticket) –
jede Zone rechnet unabhängig mit ihrer eigenen Hülle und ihrem eigenen
Nutzungsprofil; Trennwände zählen implizit als adiabat, wie es der bestehende
Rechenkern für "Wand an beheizten Nachbarraum" (F_x = 0) ohnehin schon vorsieht.

Der dominante Effekt einer Zonierung – unterschiedliche interne Gewinne,
Luftwechsel und Solltemperatur je Nutzungsprofil (Teil 10) – wird damit bereits
korrekt abgebildet; nur die (i. d. R. kleinere) zusätzliche Kopplung über die
Trennwandfläche selbst fehlt noch.

Konsistenz-Eigenschaft (für Tests genutzt): da H_T, H_V, solare/interne Gewinne
linear in Fläche/BGF sind und der Ausnutzungsgrad η nur vom Verhältnis
Q_Quelle/Q_Senke abhängt (skaleninvariant), liefert die Aufteilung eines
gleichförmigen Gebäudes in N identische Zonen (gleiches Profil, proportional
geteilte Hülle) exakt dasselbe Gesamtergebnis wie die Einzonen-Rechnung fürs
ganze Gebäude.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..utils import safe_float
from .din18599 import MONTH_NAMES, calculate_heat_demand


def calculate_heat_demand_multizone(zones: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Führt calculate_heat_demand() unverändert je Zone aus und aggregiert.

    zones: Liste von Eingabe-Dicts, je Eintrag im selben Format, das
    calculate_heat_demand() für eine Einzelzonen-Rechnung erwartet (bgf,
    {orientation}_area/_u, window_*_area, building_type_variant, ...).
    Optional je Zone: "zone_name" für die Ergebnis-Beschriftung.
    """
    if not zones:
        return {"ok": False, "errors": ["Keine Zonen übergeben."]}

    zone_results: List[Dict[str, Any]] = []
    errors: List[str] = []
    bgf_by_zone: List[float] = []
    for i, zdata in enumerate(zones):
        name = zdata.get("zone_name") or f"Zone {i + 1}"
        r = calculate_heat_demand(zdata)
        if not r.get("ok"):
            errors.extend(f"{name}: {e}" for e in r.get("errors", []))
            continue
        r = dict(r)
        r["zone_name"] = name
        zone_results.append(r)
        bgf_by_zone.append(safe_float(zdata.get("bgf"), 0.0))

    if errors:
        return {"ok": False, "errors": errors}

    n_months = 12
    monthly_agg = [
        {"month": MONTH_NAMES[m], "q_sink": 0.0, "q_solar": 0.0, "q_internal": 0.0, "q_heat": 0.0}
        for m in range(n_months)
    ]
    bgf_total = sum(bgf_by_zone)
    h_t_total = h_v_total = 0.0
    q_sink_total = q_solar_total = q_internal_total = q_h_total = 0.0

    for r in zone_results:
        h_t_total += r["h_transmission"]
        h_v_total += r["h_ventilation"]
        q_sink_total += r["annual_heat_demand_kwh"]
        q_solar_total += r["solar_gain_kwh"]
        q_internal_total += r["internal_gain_kwh"]
        q_h_total += r["adjusted_heat_demand_kwh"]
        for m in range(n_months):
            zm = r["monthly"][m]
            monthly_agg[m]["q_sink"] += zm["q_sink"]
            monthly_agg[m]["q_solar"] += zm["q_solar"]
            monthly_agg[m]["q_internal"] += zm["q_internal"]
            monthly_agg[m]["q_heat"] += zm["q_heat"]

    specific = q_h_total / bgf_total if bgf_total > 0 else 0.0

    return {
        "ok": True,
        "zone_count": len(zone_results),
        "zones": zone_results,
        "bgf_total": round(bgf_total, 1),
        "h_transmission": round(h_t_total, 2),
        "h_ventilation": round(h_v_total, 2),
        "h_total": round(h_t_total + h_v_total, 2),
        "annual_heat_demand_kwh": round(q_sink_total, 1),
        "solar_gain_kwh": round(q_solar_total, 1),
        "internal_gain_kwh": round(q_internal_total, 1),
        "adjusted_heat_demand_kwh": round(q_h_total, 1),
        "specific_heat_demand": round(specific, 2),
        "monthly": [
            {
                "month": m["month"],
                "q_sink": round(m["q_sink"], 1),
                "q_solar": round(m["q_solar"], 1),
                "q_internal": round(m["q_internal"], 1),
                "q_heat": round(m["q_heat"], 1),
            }
            for m in monthly_agg
        ],
        "calculation_basis": (
            "DIN V 18599-2:2018-09, Monatsbilanzverfahren je Zone (Teil-10-Nutzungsprofil je "
            "Zone), zonenweise aggregiert. Trennwand-Kopplung zwischen Zonen unterschiedlicher "
            "Solltemperatur noch nicht modelliert (Phase Z2b)."
        ),
    }
