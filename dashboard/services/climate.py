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

Vereinfachung (Stufe 2): eine Klimaregion je Bundesland (16 Regionen) statt der
15 TRY-Regionen der DIN. Die Faktoren sind aus den DWD-Jahresmitteln der
Globalstrahlung (~1000 kWh/m²a Referenz Potsdam) und Lufttemperatur abgeleitet
(Flächenmittel je Bundesland, gerundet).
"""
from __future__ import annotations

from typing import Dict


# Klimaregionen je Bundesland (label + Wirkfaktoren gegenüber Referenz Potsdam
# = 1,0 / 0,0 K). radiation_factor: DWD-Globalstrahlung relativ zu Potsdam;
# temp_offset_k: Jahresmittel-Offset der Lufttemperatur (ohne Höheneffekt –
# der kommt separat über die Höhenkorrektur, sonst Doppelzählung).
REGIONS: Dict[str, Dict[str, object]] = {
    "schleswig-holstein": {"label": "Schleswig-Holstein (Küste, maritim)",
                           "radiation_factor": 0.96, "temp_offset_k": 0.3},
    "hamburg":            {"label": "Hamburg (maritim)",
                           "radiation_factor": 0.94, "temp_offset_k": 0.4},
    "bremen":             {"label": "Bremen (maritim)",
                           "radiation_factor": 0.93, "temp_offset_k": 0.4},
    "niedersachsen":      {"label": "Niedersachsen (Tiefland, maritim geprägt)",
                           "radiation_factor": 0.94, "temp_offset_k": 0.3},
    "mecklenburg-vorpommern": {"label": "Mecklenburg-Vorpommern (Ostseeküste, sonnig-kühl)",
                           "radiation_factor": 0.99, "temp_offset_k": -0.1},
    "berlin":             {"label": "Berlin (kontinental, Referenznähe)",
                           "radiation_factor": 1.00, "temp_offset_k": 0.3},
    "brandenburg":        {"label": "Brandenburg (Referenzklima Potsdam)",
                           "radiation_factor": 1.00, "temp_offset_k": 0.0},
    "sachsen-anhalt":     {"label": "Sachsen-Anhalt (kontinental, trocken)",
                           "radiation_factor": 0.99, "temp_offset_k": 0.1},
    "sachsen":            {"label": "Sachsen (kontinental)",
                           "radiation_factor": 1.00, "temp_offset_k": -0.2},
    "thueringen":         {"label": "Thüringen (Mittelgebirge, kühler)",
                           "radiation_factor": 0.97, "temp_offset_k": -0.5},
    "nordrhein-westfalen": {"label": "Nordrhein-Westfalen (mild, strahlungsarm)",
                           "radiation_factor": 0.92, "temp_offset_k": 0.8},
    "hessen":             {"label": "Hessen (Mittelgebirge, mild)",
                           "radiation_factor": 0.96, "temp_offset_k": 0.3},
    "rheinland-pfalz":    {"label": "Rheinland-Pfalz (Rheintal, mild)",
                           "radiation_factor": 0.99, "temp_offset_k": 0.6},
    "saarland":           {"label": "Saarland (mild, sonnig)",
                           "radiation_factor": 1.00, "temp_offset_k": 0.5},
    "baden-wuerttemberg": {"label": "Baden-Württemberg (strahlungsreich)",
                           "radiation_factor": 1.08, "temp_offset_k": 0.0},
    "bayern":             {"label": "Bayern (kontinental, strahlungsreich)",
                           "radiation_factor": 1.10, "temp_offset_k": -0.4},
}

DEFAULT_REGION = "brandenburg"

# Bundesland → Klimaregion (1:1)
STATE_TO_REGION: Dict[str, str] = {
    "Schleswig-Holstein": "schleswig-holstein",
    "Hamburg": "hamburg",
    "Bremen": "bremen",
    "Niedersachsen": "niedersachsen",
    "Mecklenburg-Vorpommern": "mecklenburg-vorpommern",
    "Berlin": "berlin",
    "Brandenburg": "brandenburg",
    "Sachsen-Anhalt": "sachsen-anhalt",
    "Sachsen": "sachsen",
    "Thüringen": "thueringen",
    "Nordrhein-Westfalen": "nordrhein-westfalen",
    "Rheinland-Pfalz": "rheinland-pfalz",
    "Saarland": "saarland",
    "Hessen": "hessen",
    "Bayern": "bayern",
    "Baden-Württemberg": "baden-wuerttemberg",
}


def resolve_region(state: str | None) -> Dict[str, object]:
    """Liefert die Klimaregion-Daten zum Bundesland (Fallback: Referenz Potsdam)."""
    key = STATE_TO_REGION.get((state or "").strip(), DEFAULT_REGION)
    region = dict(REGIONS[key])
    region["key"] = key
    return region
