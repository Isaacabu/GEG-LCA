"""
IFC-Import (Phase I1 der Import-Vision): reine Grunddaten-Extraktion.

Liest ein hochgeladenes IFC-Modell mit ifcopenshell und extrahiert nur die
Basisdaten, die "Gebäudedaten" vorausfüllen können: Projekt-/Gebäudename, Anzahl
Geschosse (IfcBuildingStorey), Brutto-Grundfläche (best-effort aus IfcSpace-
Mengen). KEINE Wand-/Fenster-/Grundriss-Geometrie-Extraktion — das ist Phase I2
(Folgeticket). Grund: IFC-Modelle aus unterschiedlicher Quellsoftware (Revit,
ArchiCAD, ...) sind strukturell sehr heterogen; eine verlässliche automatische
Vollgeometrie-Übernahme ist kein Ein-Schritt-Vorhaben. Der Grundriss wird nach
diesem Import weiterhin im "Komplexe Geometrie"-Editor nachgezeichnet — dieser
Schritt erspart nur das manuelle Eintragen der Eckdaten.
"""
from __future__ import annotations

import tempfile
from typing import Any, Dict, List

import ifcopenshell


class IfcImportError(Exception):
    """Datei ist keine lesbare IFC-Datei oder enthält keine verwertbaren Daten."""


def extract_basic_data(file_bytes: bytes) -> Dict[str, Any]:
    if not file_bytes:
        raise IfcImportError("Leere Datei.")

    with tempfile.NamedTemporaryFile(suffix=".ifc", delete=True) as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        try:
            model = ifcopenshell.open(tmp.name)
        except Exception as e:
            raise IfcImportError(f"Datei konnte nicht als IFC gelesen werden: {e}")

    warnings: List[str] = []

    buildings = model.by_type("IfcBuilding")
    projects = model.by_type("IfcProject")
    name = None
    if buildings and buildings[0].Name:
        name = buildings[0].Name
    elif projects and projects[0].Name:
        name = projects[0].Name
    if not name:
        name = "IFC-Import"
        warnings.append("Kein Gebäude-/Projektname im IFC-Modell gefunden.")

    storeys = model.by_type("IfcBuildingStorey")
    n_storeys = len(storeys)
    if n_storeys == 0:
        warnings.append("Keine Geschosse (IfcBuildingStorey) im Modell gefunden.")

    bgf = _sum_space_areas(model)
    if bgf <= 0:
        warnings.append(
            "Keine Flächenangaben (IfcSpace-Mengen) im Modell gefunden — Grundfläche bitte manuell eintragen."
        )

    return {
        "building_name": name,
        "storeys": n_storeys,
        "bgf": round(bgf, 1) if bgf > 0 else None,
        "warnings": warnings,
        "schema": model.schema,
    }


def _sum_space_areas(model) -> float:
    total = 0.0
    for space in model.by_type("IfcSpace"):
        total += _quantity_area(space)
    return total


def _quantity_area(product) -> float:
    """Sucht GrossFloorArea/NetFloorArea/GrossArea in den IfcElementQuantity-Mengen
    eines Produkts (Standardweg für Flächenangaben in IFC, IFC4 §IfcSpace)."""
    for rel in getattr(product, "IsDefinedBy", None) or []:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        prop_set = rel.RelatingPropertyDefinition
        if not prop_set or not prop_set.is_a("IfcElementQuantity"):
            continue
        for q in prop_set.Quantities or []:
            if q.is_a("IfcQuantityArea") and q.Name in ("GrossFloorArea", "NetFloorArea", "GrossArea"):
                return float(q.AreaValue)
    return 0.0
