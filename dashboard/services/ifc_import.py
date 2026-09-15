"""
IFC-Import: Grunddaten-Extraktion (Phase I1) + Geometrie-Extraktion für den
BIM-Viewer-Tab (Phase I2).

Phase I1 liest nur die Basisdaten, die "Gebäudedaten" vorausfüllen können:
Projekt-/Gebäudename, Anzahl Geschosse (IfcBuildingStorey), Brutto-Grundfläche
(best-effort aus IfcSpace-Mengen). Phase I2 trianguliert die sichtbaren Bauteile
(Wände/Decken/Dach/Fenster/Türen/...) für eine reine 3D-Vorschau (BIM-Viewer-Tab).

Bewusst NICHT enthalten: eine automatische Übernahme der IFC-Geometrie in den
"Komplexe Geometrie"-Grundriss-Editor (Wandflächen je Orientierung, U-Werte,
NGF-Herleitung etc.) — dafür ist IFC-Geometrie aus unterschiedlicher
Quellsoftware (Revit, ArchiCAD, ...) zu heterogen für eine verlässliche
automatische Zuordnung in einem ersten Schritt. Der BIM-Viewer zeigt das Modell
nur an (Qualitätskontrolle "was wurde importiert"); der Grundriss wird weiterhin
manuell im bestehenden Editor nachgezeichnet.
"""
from __future__ import annotations

import tempfile
from typing import Any, Dict, List

import ifcopenshell
import ifcopenshell.geom

# Bauteiltypen, die der BIM-Viewer darstellt, und ihre Farbe (0xRRGGBB) — an das
# bestehende COL-Farbschema des 3D-Hausmodells angelehnt (index.html, COL-Objekt),
# damit Viewer und Haus-Modell farblich konsistent wirken.
_VIEWER_TYPES = (
    "IfcWall", "IfcWallStandardCase", "IfcCurtainWall",
    "IfcSlab", "IfcRoof", "IfcCovering",
    "IfcWindow", "IfcDoor",
    "IfcColumn", "IfcBeam", "IfcStair", "IfcRailing",
)
_TYPE_COLOR = {
    "IfcWall": 0x2b4a78, "IfcWallStandardCase": 0x2b4a78, "IfcCurtainWall": 0x2b4a78,
    "IfcSlab": 0x0c1a30, "IfcRoof": 0x10b981, "IfcCovering": 0x10b981,
    "IfcWindow": 0xf6b94b, "IfcDoor": 0x34d399,
    "IfcColumn": 0x64748b, "IfcBeam": 0x64748b, "IfcStair": 0x64748b, "IfcRailing": 0x64748b,
}
_DEFAULT_COLOR = 0x9aa5b1
DEFAULT_MAX_ELEMENTS = 800   # Performance-Schutz gegen sehr große Modelle (Phase I2, v1)


class IfcImportError(Exception):
    """Datei ist keine lesbare IFC-Datei oder enthält keine verwertbaren Daten."""


def _open_model(file_bytes: bytes):
    if not file_bytes:
        raise IfcImportError("Leere Datei.")
    with tempfile.NamedTemporaryFile(suffix=".ifc", delete=True) as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        try:
            return ifcopenshell.open(tmp.name)
        except Exception as e:
            raise IfcImportError(f"Datei konnte nicht als IFC gelesen werden: {e}")


def extract_basic_data(file_bytes: bytes) -> Dict[str, Any]:
    return _extract_basic_data(_open_model(file_bytes))


def extract_geometry(file_bytes: bytes, max_elements: int = DEFAULT_MAX_ELEMENTS) -> Dict[str, Any]:
    return _extract_geometry(_open_model(file_bytes), max_elements)


def extract_all(file_bytes: bytes, max_elements: int = DEFAULT_MAX_ELEMENTS) -> Dict[str, Any]:
    """Öffnet die Datei nur EINMAL und liefert Grunddaten + Geometrie zusammen —
    genutzt vom Upload-View, damit dieselbe Datei nicht zweimal geparst wird."""
    model = _open_model(file_bytes)
    basic = _extract_basic_data(model)
    geo = _extract_geometry(model, max_elements)
    basic["geometry"] = geo
    basic["warnings"] = basic["warnings"] + geo.pop("warnings")
    return basic


def _extract_basic_data(model) -> Dict[str, Any]:
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


def _extract_geometry(model, max_elements: int) -> Dict[str, Any]:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    elements = []
    seen_ids = set()
    for ifc_type in _VIEWER_TYPES:
        for el in model.by_type(ifc_type):
            if el.id() in seen_ids:   # Subtypen können sich in by_type()-Aufrufen überschneiden
                continue
            seen_ids.add(el.id())
            elements.append(el)

    warnings: List[str] = []
    if not elements:
        warnings.append("Keine darstellbaren Bauteile (Wände/Decken/Fenster/...) im Modell gefunden.")

    truncated = len(elements) > max_elements
    if truncated:
        warnings.append(
            f"Modell hat {len(elements)} Bauteile — nur die ersten {max_elements} werden im BIM-Viewer angezeigt."
        )

    meshes = []
    skipped = 0
    for product in elements[:max_elements]:
        try:
            shape = ifcopenshell.geom.create_shape(settings, product)
        except Exception:
            skipped += 1
            continue
        meshes.append({
            "id": product.id(),
            "type": product.is_a(),
            "name": product.Name or product.is_a(),
            "vertices": list(shape.geometry.verts),
            "faces": list(shape.geometry.faces),
            "color": _TYPE_COLOR.get(product.is_a(), _DEFAULT_COLOR),
        })
    if skipped:
        warnings.append(f"{skipped} Bauteil(e) ohne auswertbare Geometrie übersprungen.")

    return {
        "meshes": meshes,
        "element_count": len(elements),
        "rendered_count": len(meshes),
        "warnings": warnings,
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
