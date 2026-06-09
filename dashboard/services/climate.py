"""
Standort- und Klimaregion-Auflösung.

Die DIN-V-18599-Rechenkerne (Heizwärmebedarf, PV) arbeiten intern mit dem
Referenzklima Deutschland (Potsdam, Teil 10 Tab. E.6). Damit der gewählte
**Standort** die Ergebnisse beeinflusst, ordnet dieses Modul jedem Bundesland
eine vereinfachte Klimaregion zu mit:

- ``radiation_factor`` – skaliert die monatliche Solarstrahlung der Potsdam-
  Referenz auf das regionale Jahres-Globalstrahlungsniveau (DWD-Mittel).
  Wirkt auf die solaren Gewinne der Heizbilanz **und** den PV-Ertrag.
- ``temp_offset_k`` – mittlerer Jahres-Offset der Außenlufttemperatur gegenüber
  der Potsdam-Referenz (maritim/kontinental). Die *höhenbedingte* Abkühlung wird
  separat über die Höhenlage (Höhenkorrektur, Teil 10 Anhang E) erfasst – hier
  also bewusst NICHT enthalten, um Doppelzählung zu vermeiden.

Bewusste Vereinfachung (Stufe 1): vier zusammengefasste Regionen statt der 15
TRY-Regionen der DIN. Die Faktoren sind aus den DWD-Jahresmitteln der
Globalstrahlung (~1000 kWh/m²a Referenz Potsdam) und Lufttemperatur abgeleitet.
"""
from __future__ import annotations

from typing import Dict


# Klimaregionen (label + Wirkfaktoren gegenüber Referenz Potsdam = 1,0 / 0,0)
REGIONS: Dict[str, Dict[str, object]] = {
    "nord": {"label": "Region Nord (Küste/Norddeutschland)",
             "radiation_factor": 0.93, "temp_offset_k": 0.3},
    "ost":  {"label": "Region Ost (Referenzklima Potsdam)",
             "radiation_factor": 1.00, "temp_offset_k": 0.0},
    "west": {"label": "Region West (Rheinland/mild)",
             "radiation_factor": 1.00, "temp_offset_k": 1.0},
    "sued": {"label": "Region Süd (Süddeutschland)",
             "radiation_factor": 1.10, "temp_offset_k": -0.3},
}

DEFAULT_REGION = "ost"

# Bundesland → Klimaregion
STATE_TO_REGION: Dict[str, str] = {
    "Schleswig-Holstein": "nord",
    "Hamburg": "nord",
    "Bremen": "nord",
    "Niedersachsen": "nord",
    "Mecklenburg-Vorpommern": "nord",
    "Berlin": "ost",
    "Brandenburg": "ost",
    "Sachsen-Anhalt": "ost",
    "Sachsen": "ost",
    "Thüringen": "ost",
    "Nordrhein-Westfalen": "west",
    "Rheinland-Pfalz": "west",
    "Saarland": "west",
    "Hessen": "west",
    "Bayern": "sued",
    "Baden-Württemberg": "sued",
}


def resolve_region(state: str | None) -> Dict[str, object]:
    """Liefert die Klimaregion-Daten zum Bundesland (Fallback: Referenz Potsdam)."""
    key = STATE_TO_REGION.get((state or "").strip(), DEFAULT_REGION)
    region = dict(REGIONS[key])
    region["key"] = key
    return region
