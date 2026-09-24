"""
IFC-Import: Grunddaten (Phase I1) + Geometrie für den BIM-Viewer (Phase I2) +
Gebäudehüllen-Extraktion für die Energiebilanz (Phase I3).

Phase I1 liest nur Basisdaten (Name/Geschosse/BGF). Phase I2 trianguliert die
sichtbaren Bauteile für die reine 3D-Vorschau. Phase I3 (dieses Modul,
extract_envelope) geht einen Schritt weiter: Außenwandflächen je Himmelsrichtung,
Fenster-/Türflächen je Wand-Orientierung und Dach-/Bodenfläche — im selben
Format, das dashboard/services/din18599.py (calculate_heat_demand) erwartet
({orientation}_area/_u, window_{orientation}_area, ...). Das Frontend zeigt diese
Werte in "Gebäudehülle" als überschreibbaren Vorschlag ("Aus IFC übernommen"),
NICHT als automatische, unsichtbare Übernahme.

Methodik (bewusste Vereinfachungen, siehe auch Docstrings der Helfer unten):
- Fläche: bevorzugt aus den IFC-eigenen Mengen (Qto_*BaseQuantities), sonst
  geometrisch aus Länge × Höhe der Wand (Bounding-Box-Ansatz) - NICHT als Summe
  aller Dreiecksflächen (das würde beide Wandseiten + Kanten mitzählen und die
  Fläche massiv überschätzen).
- Außen/Innen: bevorzugt IsExternal-Eigenschaft (Pset_WallCommon); ohne diese
  Eigenschaft ein geometrischer Fallback über die Gebäude-Hüllkurve (shapely
  Convex Hull aller Wand-Endpunkte) - Wände nahe am Rand gelten als außen.
- Orientierung: Normalenvektor der Wand (senkrecht zur Längsachse), Richtung
  (welche der zwei Senkrechten "außen" ist) über den Gebäude-Schwerpunkt
  disambiguiert. Nordrichtung: IfcGeometricRepresentationContext.TrueNorth falls
  gesetzt, sonst Annahme Modell-Y-Achse = Norden (dokumentierte Vereinfachung,
  IFC hat keine verpflichtende Nordkonvention).
- Fenster/Tür → Wirtswand: über die offiziellen IFC-Beziehungen
  IfcRelFillsElement (Öffnung → Fenster/Tür) + IfcRelVoidsElement
  (Wand → Öffnung) - nicht Geometrie-Nähe-Raten.
- U-Werte werden NICHT aus IFC übernommen (die meisten Modelle tragen keine) -
  bleiben Default/manuelle Eingabe, klar als solche gekennzeichnet.
"""
from __future__ import annotations

import math
import tempfile
from typing import Any, Dict, List, Optional, Tuple

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


def extract_envelope(file_bytes: bytes) -> Dict[str, Any]:
    return _extract_envelope(_open_model(file_bytes))


def extract_all(file_bytes: bytes, max_elements: int = DEFAULT_MAX_ELEMENTS) -> Dict[str, Any]:
    """Öffnet die Datei nur EINMAL und liefert Grunddaten + Geometrie + Gebäudehülle
    zusammen — genutzt vom Upload-View, damit dieselbe Datei nicht mehrfach geparst wird."""
    model = _open_model(file_bytes)
    basic = _extract_basic_data(model)
    geo = _extract_geometry(model, max_elements)
    envelope = _extract_envelope(model)
    basic["geometry"] = geo
    basic["envelope"] = envelope
    basic["warnings"] = basic["warnings"] + geo.pop("warnings") + envelope.pop("warnings")
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


def _quantity_area(product, names=("GrossFloorArea", "NetFloorArea", "GrossArea")) -> float:
    """Sucht eine benannte Flächen-Menge in den IfcElementQuantity-Mengen eines
    Produkts (Standardweg für Flächenangaben in IFC, z.B. Qto_WallBaseQuantities
    NetSideArea, Qto_SlabBaseQuantities NetArea, IfcSpace GrossFloorArea)."""
    for rel in getattr(product, "IsDefinedBy", None) or []:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        prop_set = rel.RelatingPropertyDefinition
        if not prop_set or not prop_set.is_a("IfcElementQuantity"):
            continue
        for q in prop_set.Quantities or []:
            if q.is_a("IfcQuantityArea") and q.Name in names:
                return float(q.AreaValue)
    return 0.0


def _is_external(product) -> Optional[bool]:
    """IsExternal aus Pset_WallCommon/Pset_SlabCommon/Pset_RoofCommon, falls gesetzt.
    None = keine Angabe im Modell (Aufrufer muss dann geometrisch schätzen)."""
    for rel in getattr(product, "IsDefinedBy", None) or []:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pset = rel.RelatingPropertyDefinition
        if not pset or not pset.is_a("IfcPropertySet"):
            continue
        if not (pset.Name or "").endswith("Common"):
            continue
        for prop in pset.HasProperties or []:
            if prop.is_a("IfcPropertySingleValue") and prop.Name == "IsExternal" and prop.NominalValue is not None:
                return bool(prop.NominalValue.wrappedValue)
    return None


def _host_wall(opening_element_product) -> Optional[Any]:
    """Fenster/Tür → Wirtswand über die offiziellen IFC-Beziehungen:
    IfcWindow/IfcDoor --FillsVoids--> IfcRelFillsElement --RelatingOpeningElement-->
    IfcOpeningElement --VoidsElements--> IfcRelVoidsElement --RelatingBuildingElement--> IfcWall."""
    for rel in getattr(opening_element_product, "FillsVoids", None) or []:
        if not rel.is_a("IfcRelFillsElement"):
            continue
        opening = rel.RelatingOpeningElement
        for vrel in getattr(opening, "VoidsElements", None) or []:
            if vrel.is_a("IfcRelVoidsElement"):
                return vrel.RelatingBuildingElement
    return None


def _true_north_offset_deg(model) -> float:
    """Winkel [Grad] zwischen Modell-Y-Achse und Norden, aus
    IfcGeometricRepresentationContext.TrueNorth (falls gesetzt). 0 = Modell-Y = Norden
    (dokumentierte Vereinfachung ohne TrueNorth - IFC hat keine Pflicht-Nordkonvention)."""
    for ctx in model.by_type("IfcGeometricRepresentationContext"):
        tn = getattr(ctx, "TrueNorth", None)
        if tn is not None and getattr(tn, "DirectionRatios", None):
            dx, dy = tn.DirectionRatios[0], tn.DirectionRatios[1]
            if abs(dx) > 1e-9 or abs(dy) > 1e-9:
                return math.degrees(math.atan2(dx, dy))
    return 0.0


_ORIENTATION_KEYS = ("north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest")


def _orientation_from_vector(dx: float, dy: float, north_offset_deg: float) -> str:
    angle = (_angle_from_vector(dx, dy) - north_offset_deg + 360) % 360
    return _ORIENTATION_KEYS[round(angle / 45) % 8]


def _angle_from_vector(dx: float, dy: float) -> float:
    """Rohwinkel einer Außen-Normale zur Modell-Y-Achse, 0 = Modell-Y."""
    return (math.degrees(math.atan2(dx, dy)) + 360) % 360


def _wall_length_height_dir(verts: List[float]) -> Tuple[float, float, Tuple[float, float], Tuple[float, float]]:
    """Nähert eine Wand als Box: Länge (größter Abstand zweier Punkte in der
    XY-Projektion - robust für die box-förmigen Extrusionen, die IFC-Wände i.d.R.
    sind), Höhe (Z-Spanne), Richtungsvektor der Länge, Mittelpunkt (XY). Reine
    Geometrie-Näherung für den Fall, dass keine Qto-Menge vorliegt."""
    pts = [(verts[i], verts[i + 1], verts[i + 2]) for i in range(0, len(verts), 3)]
    zs = [p[2] for p in pts]
    height = max(zs) - min(zs) if pts else 0.0
    best_d2, best_pair = 0.0, None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dx, dy = pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]
            d2 = dx * dx + dy * dy
            if d2 > best_d2:
                best_d2, best_pair = d2, (i, j)
    if not best_pair or best_d2 < 1e-9:
        return 0.0, height, (0.0, 0.0), (0.0, 0.0)
    length = best_d2 ** 0.5
    i, j = best_pair
    p1, p2 = pts[i], pts[j]
    direction = ((p2[0] - p1[0]) / length, (p2[1] - p1[1]) / length)
    midpoint = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
    return length, height, direction, midpoint


def _triangle_normal_area(
    p0: Tuple[float, float, float], p1: Tuple[float, float, float], p2: Tuple[float, float, float]
) -> Tuple[Tuple[float, float, float], float]:
    """Kreuzprodukt zweier Kantenvektoren eines Dreiecks -> (Einheits-)Normale + Fläche."""
    e1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    e2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
    cx = e1[1] * e2[2] - e1[2] * e2[1]
    cy = e1[2] * e2[0] - e1[0] * e2[2]
    cz = e1[0] * e2[1] - e1[1] * e2[0]
    norm = math.sqrt(cx * cx + cy * cy + cz * cz)
    if norm < 1e-9:
        return (0.0, 0.0, 0.0), 0.0
    return (cx / norm, cy / norm, cz / norm), norm / 2.0


def _roof_top_plane(verts: List[float], faces: List[int]) -> Optional[Dict[str, Any]]:
    """Ebene der Dach-OBERSEITE eines triangulierten Slab-/Roof-Meshes.

    IFC-Exporte liefern Dachflächen i.d.R. als Prisma (Oberseite + Unterseite + dünne
    Rand-/Giebelstreifen für die Plattendicke, siehe Modell AC20-FZK-Haus.ifc: je Dach-
    Slab 8 Punkte/12 Dreiecke). Eine Best-Fit-Ebene durch ALLE Punkte würde durch die
    (leicht höhenversetzte) Unterseite verzerrt. Trennung daher über die Dreiecks-
    Normalen: nur Dreiecke mit nach oben zeigender Normale (normal.z > 0 - schließt die
    Unterseite [normal.z < 0] und die näherungsweise senkrechten Rand-/Giebeldreiecke
    [normal.z ≈ 0] aus) zählen als Oberseite; ihre Normalen werden flächengewichtet
    gemittelt (deckt minimale Triangulierungs-Abweichungen der Oberseiten-Dreiecke ab).

    Vereinfachung (dokumentierte Grenze, kein Bug): geht von EINER Dachebene je Element
    aus. Passt zum üblichen Satteldach-Export als 2 Einzel-Slabs (je eine Dachseite ein
    eigenes Element - siehe AC20-FZK-Haus.ifc). Ein komplexeres Walm-/Krüppelwalmdach,
    das als EIN IfcRoof-Element mit mehreren echten Dachflächen exportiert wird, würde
    hier fälschlich zu einer gemittelten Ebene über alle Flächen führen.
    """
    pts = [(verts[i], verts[i + 1], verts[i + 2]) for i in range(0, len(verts), 3)]
    area_sum = 0.0
    nx_sum = ny_sum = nz_sum = 0.0
    top_pts: List[Tuple[float, float, float]] = []
    for i in range(0, len(faces), 3):
        p0, p1, p2 = pts[faces[i]], pts[faces[i + 1]], pts[faces[i + 2]]
        normal, area = _triangle_normal_area(p0, p1, p2)
        if area <= 1e-9 or normal[2] <= 1e-6:
            continue
        area_sum += area
        nx_sum += normal[0] * area
        ny_sum += normal[1] * area
        nz_sum += normal[2] * area
        top_pts.extend((p0, p1, p2))
    if area_sum <= 1e-9:
        return None
    nlen = math.sqrt(nx_sum ** 2 + ny_sum ** 2 + nz_sum ** 2)
    if nlen < 1e-9:
        return None
    normal = (nx_sum / nlen, ny_sum / nlen, nz_sum / nlen)
    return {"normal": normal, "area": area_sum, "points": top_pts}


def _roof_pitch_azimuth(
    normal: Tuple[float, float, float], north_offset_deg: float
) -> Tuple[float, Optional[float], Optional[str]]:
    """Neigung + Ausrichtung einer Dachebene aus ihrer (nach oben zeigenden) Normale.

    Neigung (pitch_deg): Winkel zur Vertikalen, 0° = Flachdach, 90° = wandsenkrecht -
    acos(normal.z).
    Ausrichtung: Kompassrichtung der horizontalen Normalen-Komponente (= die Richtung,
    in die auf dieser Dachfläche flach aufliegende PV-Module zeigen würden), über
    dieselben Helfer wie bei Wänden (_orientation_from_vector/_angle_from_vector,
    inkl. TrueNorth-Offset) in Kompass-Grad umgerechnet und dann in die App-Konvention
    von #pv_roof_azimuth (0° = Süd, negativ = Ost, positiv = West, ±180° = Nord)
    übersetzt. Bei (nahezu) Flachdach ist die horizontale Komponente numerisch
    instabil/bedeutungslos -> azimuth_deg/orientation bleiben None (die Ausrichtung
    entscheidet dort ohnehin die Aufständerung, nicht die Dachebene selbst).
    """
    nz = max(-1.0, min(1.0, normal[2]))
    pitch_deg = math.degrees(math.acos(nz))
    nx, ny = normal[0], normal[1]
    if math.hypot(nx, ny) < 1e-3:
        return pitch_deg, None, None
    orientation = _orientation_from_vector(nx, ny, north_offset_deg)
    compass_deg = (_angle_from_vector(nx, ny) - north_offset_deg + 360) % 360
    azimuth_deg = compass_deg - 180.0   # 0=Süd, negativ=Ost, positiv=West (s. Docstring)
    return pitch_deg, azimuth_deg, orientation


def _plane_hull_area(points: List[Tuple[float, float, float]], normal: Tuple[float, float, float]) -> Optional[float]:
    """2D-Fläche der konvexen Hülle der auf die Dachebene projizierten Oberseiten-
    Punkte - dieselbe Projektions-/Convex-Hull-Methodik wie beim Fußabdruck/den Räumen
    weiter unten (footprint/rooms), hier als geometrischer Fallback/Cross-Check zur
    Qto-Fläche (bleibt primäre Quelle, s. Modul-Docstring), NICHT als deren Ersatz."""
    if len(points) < 3:
        return None
    origin = points[0]
    ref = (0.0, 0.0, 1.0) if abs(normal[2]) < 0.9 else (1.0, 0.0, 0.0)
    ux = ref[1] * normal[2] - ref[2] * normal[1]
    uy = ref[2] * normal[0] - ref[0] * normal[2]
    uz = ref[0] * normal[1] - ref[1] * normal[0]
    ulen = math.sqrt(ux * ux + uy * uy + uz * uz)
    if ulen < 1e-9:
        return None
    u = (ux / ulen, uy / ulen, uz / ulen)
    v = (
        normal[1] * u[2] - normal[2] * u[1],
        normal[2] * u[0] - normal[0] * u[2],
        normal[0] * u[1] - normal[1] * u[0],
    )
    coords2d = []
    for p in points:
        dx, dy, dz = p[0] - origin[0], p[1] - origin[1], p[2] - origin[2]
        coords2d.append((dx * u[0] + dy * u[1] + dz * u[2], dx * v[0] + dy * v[1] + dz * v[2]))
    try:
        from shapely.geometry import MultiPoint
        hull = MultiPoint(coords2d).convex_hull
        if hull.geom_type == "Polygon":
            return hull.area
    except Exception:
        pass
    return None


def _extract_envelope(model) -> Dict[str, Any]:
    warnings: List[str] = []
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    north_offset = _true_north_offset_deg(model)
    if north_offset == 0.0:
        warnings.append(
            "Kein TrueNorth im Modell gesetzt — Nordrichtung wurde als Modell-Y-Achse angenommen; "
            "Orientierungen bitte prüfen."
        )

    wall_types = ("IfcWall", "IfcWallStandardCase")
    walls = []
    for wt in wall_types:
        walls.extend(model.by_type(wt))
    seen = set()
    walls = [w for w in walls if not (w.id() in seen or seen.add(w.id()))]

    wall_infos = []
    for wall in walls:
        try:
            shape = ifcopenshell.geom.create_shape(settings, wall)
        except Exception:
            continue
        length, height, direction, midpoint = _wall_length_height_dir(list(shape.geometry.verts))
        if length <= 0 or height <= 0:
            continue
        area = _quantity_area(wall, ("NetSideArea", "GrossSideArea"))
        if area <= 0:
            area = length * height
        wall_infos.append({
            "product": wall, "area": area, "length": length, "height": height,
            "direction": direction, "midpoint": midpoint,
            "is_external": _is_external(wall),
        })

    if not wall_infos:
        warnings.append("Keine auswertbaren Wände (IfcWall) im Modell gefunden.")
        return {
            "walls": {}, "windows": {}, "doors": {},
            "wall_elements": [], "window_elements": [], "door_elements": [],
            "roof_elements": [], "floor_elements": [],
            "roof_area": None, "floor_area": None, "footprint": [], "rooms": [],
            "warnings": warnings,
        }

    # Gebäude-Schwerpunkt (Mittel aller Wand-Mittelpunkte) - disambiguiert, welche der
    # zwei Senkrechten zur Wandrichtung "außen" ist.
    cx = sum(w["midpoint"][0] for w in wall_infos) / len(wall_infos)
    cy = sum(w["midpoint"][1] for w in wall_infos) / len(wall_infos)

    # Geometrischer Außen-Fallback nur wenn IsExternal NIRGENDS gesetzt ist (sonst wird
    # die explizite Modell-Angabe respektiert, auch wenn sie nur für einen Teil vorliegt).
    any_explicit = any(w["is_external"] is not None for w in wall_infos)
    hull = None
    if not any_explicit:
        try:
            from shapely.geometry import MultiPoint
            pts = [w["midpoint"] for w in wall_infos]
            hull = MultiPoint(pts).convex_hull if len(pts) >= 3 else None
        except Exception:
            hull = None
        warnings.append(
            "Keine IsExternal-Angabe im Modell — Außenwand-Erkennung erfolgt geometrisch "
            "über die Gebäude-Hüllkurve; bitte Ergebnis prüfen."
        )

    def _is_ext(w):
        if w["is_external"] is not None:
            return w["is_external"]
        if hull is None:
            return True
        from shapely.geometry import Point as SPoint
        return hull.boundary.distance(SPoint(w["midpoint"])) < 0.3

    wall_areas: Dict[str, float] = {}
    wall_elements: List[Dict[str, Any]] = []
    for w in wall_infos:
        if not _is_ext(w):
            continue
        dx, dy = w["direction"]
        nx, ny = -dy, dx   # senkrecht zur Wandrichtung
        # Richtung so wählen, dass sie vom Schwerpunkt WEG zeigt (= außen)
        vx, vy = w["midpoint"][0] - cx, w["midpoint"][1] - cy
        if nx * vx + ny * vy < 0:
            nx, ny = -nx, -ny
        orientation = _orientation_from_vector(nx, ny, north_offset)
        angle_deg = _angle_from_vector(nx, ny)
        wall_areas[orientation] = wall_areas.get(orientation, 0.0) + w["area"]
        w["orientation"] = orientation
        wall_elements.append({
            "id": w["product"].id(),
            "global_id": w["product"].GlobalId,
            "name": w["product"].Name or f"Wand {w['product'].id()}",
            "type": w["product"].is_a(),
            "orientation": orientation,
            "angle_deg": round(angle_deg, 3),
            "area": round(w["area"], 3),
            "length": round(w["length"], 3),
            "height": round(w["height"], 3),
        })
    if not wall_areas:
        warnings.append("Keine Außenwände erkannt — alle Wände wurden als innenliegend eingestuft.")

    # Fenster/Türen → Wirtswand-Orientierung (offizielle IFC-Beziehungen, s. _host_wall)
    wall_orientation_by_id = {w["product"].id(): w.get("orientation") for w in wall_infos}
    wall_angle_by_id = {w["id"]: w.get("angle_deg") for w in wall_elements}
    window_areas: Dict[str, float] = {}
    window_counts: Dict[str, int] = {}
    window_elements: List[Dict[str, Any]] = []
    door_elements: List[Dict[str, Any]] = []
    door_areas: Dict[str, Dict[str, Any]] = {}
    for opening_type, qty_names in (
        ("IfcWindow", ("Area", "GrossArea")),
        ("IfcDoor", ("Area", "GrossArea")),
    ):
        for product in model.by_type(opening_type):
            host = _host_wall(product)
            orientation = wall_orientation_by_id.get(host.id()) if host else None
            if not orientation:
                continue
            area = _quantity_area(product, qty_names)
            width = height = 0.0
            if area <= 0:
                try:
                    shape = ifcopenshell.geom.create_shape(settings, product)
                    width, height, _, _ = _wall_length_height_dir(list(shape.geometry.verts))
                    area = width * height
                except Exception:
                    area = 0.0
            elif area > 0:
                try:
                    shape = ifcopenshell.geom.create_shape(settings, product)
                    width, height, _, _ = _wall_length_height_dir(list(shape.geometry.verts))
                except Exception:
                    pass
            if area <= 0:
                continue
            if opening_type == "IfcWindow":
                window_areas[orientation] = window_areas.get(orientation, 0.0) + area
                window_counts[orientation] = window_counts.get(orientation, 0) + 1
                window_elements.append({
                    "id": product.id(),
                    "global_id": product.GlobalId,
                    "name": product.Name or f"Fenster {product.id()}",
                    "type": product.is_a(),
                    "host_id": host.id() if host else None,
                    "orientation": orientation,
                    "angle_deg": wall_angle_by_id.get(host.id()) if host else None,
                    "area": round(area, 3),
                    "width": round(width, 3) if width > 0 else None,
                    "height": round(height, 3) if height > 0 else None,
                })
            else:
                d = door_areas.setdefault(orientation, {"count": 0, "total_area": 0.0})
                d["count"] += 1
                d["total_area"] += area
                door_elements.append({
                    "id": product.id(),
                    "global_id": product.GlobalId,
                    "name": product.Name or f"Tür {product.id()}",
                    "type": product.is_a(),
                    "host_id": host.id() if host else None,
                    "orientation": orientation,
                    "angle_deg": wall_angle_by_id.get(host.id()) if host else None,
                    "area": round(area, 3),
                    "width": round(width, 3) if width > 0 else None,
                    "height": round(height, 3) if height > 0 else None,
                })

    doors_out = {
        o: {"count": d["count"], "area_per_unit": round(d["total_area"] / d["count"], 2)}
        for o, d in door_areas.items() if d["count"] > 0
    }

    # Dach-/Bodenfläche: erst Qto-Menge, sonst Näherung aus der Geometrie. Dächer werden
    # von mancher Exportsoftware (z.B. ArchiCAD) als IfcSlab mit PredefinedType=ROOF
    # statt als eigenes IfcRoof geführt — beide Quellen zusammenführen. Für die
    # Bodenplatte zählt NUR BASESLAB (erdberührt, wärmeverlustrelevant) - IfcSlab
    # FLOOR sind Zwischendecken zwischen Geschossen, thermisch innenliegend und
    # dürfen NICHT mitgezählt werden (sonst Boden-U-Wert-Verlust systematisch zu groß).
    # Pitch/Azimut je Dachelement (für die PV-Ertragsrechnung, s. _roof_top_plane/
    # _roof_pitch_azimuth oben): aus der Oberseiten-Normale des triangulierten Meshes,
    # NICHT aus allen 8 Prisma-Punkten (die Unterseite würde die Ebene verzerren).
    roof_area = None
    roof_elements: List[Dict[str, Any]] = []
    roof_products = list(model.by_type("IfcRoof"))
    roof_products += [s for s in model.by_type("IfcSlab") if getattr(s, "PredefinedType", None) == "ROOF"]
    for product in roof_products:
        a = _quantity_area(product, ("GrossArea", "NetArea"))
        pitch_deg = azimuth_deg = area_m2 = None
        pitch_orientation = None
        try:
            shape = ifcopenshell.geom.create_shape(settings, product)
            plane = _roof_top_plane(list(shape.geometry.verts), list(shape.geometry.faces))
            if plane:
                pitch_deg, azimuth_deg, pitch_orientation = _roof_pitch_azimuth(plane["normal"], north_offset)
                area_m2 = _plane_hull_area(plane["points"], plane["normal"])
        except Exception:
            pass
        if a <= 0 and area_m2:
            a = area_m2   # geometrischer Fallback ohne Qto-Menge (s. Modul-Docstring)
        if a > 0:
            roof_area = (roof_area or 0.0) + a
            roof_elements.append({
                "id": product.id(), "global_id": product.GlobalId,
                "name": product.Name or f"Dach {product.id()}",
                "type": product.is_a(), "orientation": "horizontal", "area": round(a, 3),
                # Neu (PV-Übernahme aus IFC-Dachgeometrie): Neigung/Ausrichtung der
                # Dachebene + Kompassrichtung + geometrische Flächen-Kontrolle. None,
                # wenn die Oberseiten-Ebene nicht bestimmbar war (z.B. entartetes Mesh)
                # bzw. bei (nahezu) Flachdach für azimuth_deg/azimuth_orientation.
                "pitch_deg": round(pitch_deg, 1) if pitch_deg is not None else None,
                "azimuth_deg": round(azimuth_deg, 1) if azimuth_deg is not None else None,
                "azimuth_orientation": pitch_orientation,
                "area_m2": round(area_m2, 3) if area_m2 is not None else None,
            })
    if roof_area is None:
        warnings.append("Kein Dach (IfcRoof/IfcSlab ROOF) mit Flächenangabe im Modell gefunden — bitte manuell eintragen.")

    floor_area = None
    floor_elements: List[Dict[str, Any]] = []
    for product in model.by_type("IfcSlab"):
        if getattr(product, "PredefinedType", None) != "BASESLAB":
            continue
        a = _quantity_area(product, ("GrossArea", "NetArea"))
        if a > 0:
            floor_area = (floor_area or 0.0) + a
            floor_elements.append({
                "id": product.id(), "global_id": product.GlobalId,
                "name": product.Name or f"Bodenplatte {product.id()}",
                "type": product.is_a(), "orientation": "horizontal", "area": round(a, 3),
            })
    if floor_area is None:
        warnings.append("Keine Bodenplatte (IfcSlab, BASESLAB) mit Flächenangabe gefunden — bitte manuell eintragen.")

    # --- Gebäude-Fußabdruck + Räume je Geschoss (Phase I4, für den Inneneinrichtung-Tab) ---
    # Fußabdruck: konvexe Hülle der Außenwand-Mittelpunkte (dieselbe Näherung wie oben für die
    # Außen/Innen-Klassifikation, hier aber immer berechnet - wir brauchen eine durchgängige
    # Fläche für den Grundriss-Editor, nicht nur eine Ja/Nein-Einstufung je Wand).
    footprint_pts: List[Dict[str, float]] = []
    try:
        from shapely.geometry import MultiPoint as _FpMultiPoint
        ext_pts = [w["midpoint"] for w in wall_infos if _is_ext(w)]
        pts_for_hull = ext_pts if len(ext_pts) >= 3 else [w["midpoint"] for w in wall_infos]
        if len(pts_for_hull) >= 3:
            fp_hull = _FpMultiPoint(pts_for_hull).convex_hull
            if fp_hull.geom_type == "Polygon":
                footprint_pts = [{"x": c[0], "y": c[1]} for c in list(fp_hull.exterior.coords)[:-1]]
    except Exception:
        footprint_pts = []

    # Geschosse: IfcBuildingStorey nach Elevation sortiert -> Index 0 = unterstes Geschoss (EG),
    # damit es zur Zählweise im Inneneinrichtung-Tab passt (dort Etage 0 = EG).
    storeys = sorted(model.by_type("IfcBuildingStorey"),
                      key=lambda s: (s.Elevation if s.Elevation is not None else 0.0))
    storey_index = {s.id(): i for i, s in enumerate(storeys)}
    element_to_storey: Dict[int, int] = {}
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        struct = rel.RelatingStructure
        if struct is None or not struct.is_a("IfcBuildingStorey"):
            continue
        idx = storey_index.get(struct.id())
        if idx is None:
            continue
        for el in rel.RelatedElements or []:
            element_to_storey[el.id()] = idx

    # Räume: IfcSpace-Grundriss als konvexe Hülle seiner Geometrie-Punkte (echte Raumkontur
    # kann konkav/L-förmig sein - die Hülle ist eine bewusste, sichere Vereinfachung, kein
    # exakter Raumumriss). Ohne IfcSpace im Modell bleibt rooms leer; der Grundriss muss dann
    # weiterhin manuell im Inneneinrichtung-Tab gezeichnet werden (kein Rückschritt ggü. vorher).
    rooms: List[Dict[str, Any]] = []
    for space in model.by_type("IfcSpace"):
        try:
            shape = ifcopenshell.geom.create_shape(settings, space)
        except Exception:
            continue
        verts = list(shape.geometry.verts)
        pts2d = [(verts[i], verts[i + 1]) for i in range(0, len(verts), 3)]
        if len(pts2d) < 3:
            continue
        try:
            from shapely.geometry import MultiPoint as _RoomMultiPoint
            hull = _RoomMultiPoint(pts2d).convex_hull
            if hull.geom_type != "Polygon":
                continue
            room_pts = [{"x": c[0], "y": c[1]} for c in list(hull.exterior.coords)[:-1]]
        except Exception:
            continue
        rooms.append({
            "floor": element_to_storey.get(space.id(), 0),
            "name": space.LongName or space.Name or f"Raum {space.id()}",
            "pts": room_pts,
        })
    if not rooms:
        warnings.append(
            "Keine Räume (IfcSpace) im Modell gefunden — Grundriss muss im "
            "Inneneinrichtung-Tab weiterhin manuell gezeichnet werden."
        )

    # Koordinaten normalisieren: kleinste x/y aus Fußabdruck+Räumen -> (0,0), passend zur
    # Konvention des Inneneinrichtung-Tabs (Gebäudeecke = Ursprung, Meter positiv, siehe
    # getFootprint() in index.html).
    all_pts = list(footprint_pts)
    for r in rooms:
        all_pts.extend(r["pts"])
    if all_pts:
        min_x = min(p["x"] for p in all_pts)
        min_y = min(p["y"] for p in all_pts)
        for p in footprint_pts:
            p["x"] = round(p["x"] - min_x, 2)
            p["y"] = round(p["y"] - min_y, 2)
        for r in rooms:
            for p in r["pts"]:
                p["x"] = round(p["x"] - min_x, 2)
                p["y"] = round(p["y"] - min_y, 2)

    return {
        "walls": {o: round(a, 1) for o, a in wall_areas.items()},
        "wall_elements": wall_elements,
        "windows": {o: round(a, 1) for o, a in window_areas.items()},
        "window_counts": {o: c for o, c in window_counts.items()},
        "window_elements": window_elements,
        "doors": doors_out,
        "door_elements": door_elements,
        "roof_elements": roof_elements,
        "floor_elements": floor_elements,
        "roof_area": round(roof_area, 1) if roof_area else None,
        "floor_area": round(floor_area, 1) if floor_area else None,
        "footprint": footprint_pts,
        "rooms": rooms,
        "warnings": warnings,
    }
