#!/usr/bin/env python
"""Verifikation des IFC-Imports (dashboard/services/ifc_import.py).

Deckt zwei Ebenen ab:
1. Echter End-to-End-Import einer realen IFC-Testdatei (AC20-FZK-Haus, offizielles
   IFC4-Beispielmodell mit Satteldach) über extract_all() — prüft Grunddaten,
   Geometrie (BIM-Viewer-Meshes) und Gebäudehülle (Wände/Fenster/Türen/Dach/Boden/
   Fußabdruck/Räume) auf Plausibilität. Die Datei liegt NICHT im Repo (zu groß/keine
   Lizenz zum Einchecken) — falls sie unter ~/Downloads/AC20-FZK-Haus.ifc fehlt, wird
   dieser Teil übersprungen (kein Fehlschlag), die reinen Geometrie-Unittests laufen
   trotzdem.
2. Reine Unittests der Geometrie-Helfer (_triangle_normal_area, _roof_top_planes,
   _roof_pitch_azimuth) mit synthetischen, analytisch nachrechenbaren Dreiecksnetzen —
   unabhängig von echten IFC-Daten, insbesondere Regressionsschutz für die
   Mehrflächen-Dachsegmentierung (Commits 1c75e4c/6ee6774: Greedy-Normalenclustering
   mit 12°-Schwellwert statt einer gemittelten Kompromiss-Ebene).

Standalone (kein Django nötig): ifc_import.py importiert nur math/tempfile/typing/
ifcopenshell — daher wie normpruefung.py per importlib geladen, OHNE django.setup().
Muss mit einem Python laufen, das ifcopenshell + shapely hat (im Repo: .venv).

Aufruf: .venv/bin/python3 scripts/verify_ifc_import.py
"""
import math
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import importlib.util


def _load():
    import types
    base = Path(__file__).resolve().parent.parent / "dashboard"
    pkg = types.ModuleType("dashboard")
    pkg.__path__ = [str(base)]
    sys.modules["dashboard"] = pkg
    spkg = types.ModuleType("dashboard.services")
    spkg.__path__ = [str(base / "services")]
    sys.modules["dashboard.services"] = spkg
    spec = importlib.util.spec_from_file_location("dashboard.services.ifc_import",
                                                  base / "services" / "ifc_import.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["dashboard.services.ifc_import"] = mod
    spec.loader.exec_module(mod)
    return mod


d = _load()
ok = True


def check(name, cond):
    global ok
    print(("  ✓ " if cond else "  ✗ ") + name)
    ok = ok and cond


# ---------------------------------------------------------------------------
# Geometrie-Hilfsfunktionen für synthetische Testnetze (unabhängig vom Modul
# unter Test nachgerechnet, nicht dessen eigene Helfer wiederverwendet).
# ---------------------------------------------------------------------------

def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _normalize(v):
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / n, v[1] / n, v[2] / n)


def _normal_from_pitch_compass(pitch_deg, compass_deg):
    """Normale für gegebene Neigung + 'Rohwinkel' (0=Modell-Y/Nord, 90=Modell-X/Ost,
    s. _angle_from_vector/_orientation_from_vector-Konvention in ifc_import.py, hier
    unabhängig nachgebaut: dx=sin(pitch)*sin(compass), dy=sin(pitch)*cos(compass),
    dz=cos(pitch))."""
    p, c = math.radians(pitch_deg), math.radians(compass_deg)
    return (math.sin(p) * math.sin(c), math.sin(p) * math.cos(c), math.cos(p))


def _rect_mesh(normal, size, center=(0.0, 0.0, 0.0)):
    """Ebenes Quadrat (Seitenlänge `size`, Fläche size²) mit EXAKT der gegebenen
    Normale, als 2 Dreiecke (analytisch konstruiert: u,v,normal bilden ein
    rechtshändiges Orthonormalsystem, cross(e1,e2) der ersten beiden Dreieckskanten
    liefert dann per Konstruktion +normal, s. Triple-Produkt-Identität). Liefert
    (verts, faces) im selben flachen Format wie ifcopenshell.geom-Shapes."""
    normal = _normalize(normal)
    ref = (0.0, 0.0, 1.0) if abs(normal[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = _normalize(_cross(ref, normal))
    v = _cross(normal, u)  # u,v,normal rechtshändig (v = normal x u)
    h = size / 2.0
    cx, cy, cz = center

    def pt(su, sv):
        return (cx + su * h * u[0] + sv * h * v[0],
                cy + su * h * u[1] + sv * h * v[1],
                cz + su * h * u[2] + sv * h * v[2])

    c0, c1, c2, c3 = pt(-1, -1), pt(1, -1), pt(1, 1), pt(-1, 1)
    verts = [*c0, *c1, *c2, *c3]
    faces = [0, 1, 2, 0, 2, 3]
    return verts, faces


def _combine(*meshes):
    verts: list = []
    faces: list = []
    offset = 0
    for vs, fs in meshes:
        verts.extend(vs)
        faces.extend(f + offset for f in fs)
        offset += len(vs) // 3
    return verts, faces


def _find_group(groups, normal, tol_dot=0.999):
    """Gruppe mit der zur erwarteten Normale nächstliegenden Normale (Dot-Produkt)."""
    normal = _normalize(normal)
    best = max(groups, key=lambda g: sum(a * b for a, b in zip(g["normal"], normal)))
    dot = sum(a * b for a, b in zip(best["normal"], normal))
    return best, dot


# ---------------------------------------------------------------------------
# Feature 1: _triangle_normal_area
# ---------------------------------------------------------------------------
print("=== Feature 1: _triangle_normal_area ===")
n, a = d._triangle_normal_area((0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (0.0, 4.0, 0.0))
check("3-4-5-Dreieck: Normale (0,0,1)", all(abs(x - y) < 1e-9 for x, y in zip(n, (0.0, 0.0, 1.0))))
check("3-4-5-Dreieck: Fläche = 6.0", abs(a - 6.0) < 1e-9)
n2, a2 = d._triangle_normal_area((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0))
check("entartetes (kollineares) Dreieck: Fläche 0", abs(a2) < 1e-9)
check("entartetes Dreieck: Normale (0,0,0)", n2 == (0.0, 0.0, 0.0))

# ---------------------------------------------------------------------------
# Feature 2: _roof_pitch_azimuth
# ---------------------------------------------------------------------------
print("=== Feature 2: _roof_pitch_azimuth ===")
pitch, azimuth, orient = d._roof_pitch_azimuth((0.0, 0.0, 1.0), 0.0)
check("Flachdach: pitch=0", abs(pitch) < 1e-9)
check("Flachdach: azimuth=None (Ausrichtung bedeutungslos)", azimuth is None)
check("Flachdach: orientation=None", orient is None)

# pitch 40°, App-Azimut -90° (Ost) -> Rohwinkel(compass) = -90+180 = 90
normal_east = _normal_from_pitch_compass(40.0, 90.0)
pitch2, azimuth2, orient2 = d._roof_pitch_azimuth(normal_east, 0.0)
check("geneigte Ebene: pitch=40° exakt nachgerechnet", abs(pitch2 - 40.0) < 1e-6)
check("geneigte Ebene: azimuth=-90° (Ost, App-Konvention)", abs(azimuth2 - (-90.0)) < 1e-6)
check("geneigte Ebene: orientation='east'", orient2 == "east")

# TrueNorth-Offset: gleiche Normale, Nord um 30° gedreht -> Kompassrichtung verschiebt
# sich entsprechend (Rohwinkel 90 -> Kompass 60 -> 'northeast', Azimut -120°)
pitch3, azimuth3, orient3 = d._roof_pitch_azimuth(normal_east, 30.0)
check("TrueNorth-Offset wirkt auf Azimut", abs(azimuth3 - (-120.0)) < 1e-6)
check("TrueNorth-Offset wirkt auf Orientierung", orient3 == "northeast")
check("TrueNorth-Offset ändert Pitch NICHT", abs(pitch3 - pitch2) < 1e-9)

# ---------------------------------------------------------------------------
# Feature 3: _roof_top_planes — Segmentierung
# ---------------------------------------------------------------------------
print("=== Feature 3a: _roof_top_planes — eine ebene Fläche + Unterseiten-Ausschluss ===")
top = _rect_mesh((0.0, 0.0, 1.0), 4.0)
bottom = _rect_mesh((0.0, 0.0, -1.0), 4.0)  # Unterseite, muss ausgeschlossen werden
verts, faces = _combine(top, bottom)
groups = d._roof_top_planes(verts, faces)
check("genau 1 Gruppe (Unterseite ausgeschlossen)", len(groups) == 1)
check("Fläche der Gruppe = 16.0 (nur Oberseite)", groups and abs(groups[0]["area"] - 16.0) < 1e-6)

# Rückwärtskompat-Wrapper
single = d._roof_top_plane(verts, faces)
check("_roof_top_plane liefert die größte (einzige) Ebene", single is not None and abs(single["area"] - 16.0) < 1e-6)
empty = d._roof_top_plane([], [])
check("_roof_top_plane liefert None bei leerem Netz", empty is None)
check("_roof_top_planes liefert [] bei leerem Netz", d._roof_top_planes([], []) == [])

print("=== Feature 3b: _roof_top_planes — synthetisches 4-Flächen-Walmdach ===")
# Pitch 45°, App-Azimute 0°(Süd)/180°(Nord)/-90°(Ost)/90°(West) — deutlich >12° auseinander
walm_targets = {"south": 0.0, "north": 180.0, "east": -90.0, "west": 90.0}
walm_meshes = []
walm_normals = {}
for label, az in walm_targets.items():
    normal = _normal_from_pitch_compass(45.0, (az + 180.0) % 360.0)
    walm_normals[label] = normal
    walm_meshes.append(_rect_mesh(normal, 5.0))
verts, faces = _combine(*walm_meshes)
groups = d._roof_top_planes(verts, faces)
check("4 Walmdach-Flächen -> genau 4 getrennte Gruppen (keine gemittelte Ebene)", len(groups) == 4)
for label, normal in walm_normals.items():
    g, dot = _find_group(groups, normal)
    check(f"Walmdach-Fläche '{label}': Normale korrekt zugeordnet (dot={dot:.4f})", dot > 0.999)
    check(f"Walmdach-Fläche '{label}': Fläche = 25.0", abs(g["area"] - 25.0) < 1e-6)

print("=== Feature 3c: _roof_top_planes — 12°-Schwellwert ===")
# Zwei Ebenen mit Normalen nur 5° auseinander (gleicher Kompass, Pitch 5°/10°) -> unter
# dem Schwellwert -> müssen zusammengefasst werden (Regressionsschutz gegen zu
# niedrig gewählten Schwellwert / gegen Rückfall in eine überempfindliche Trennung).
close_a = _rect_mesh(_normal_from_pitch_compass(5.0, 180.0), 3.0)
close_b = _rect_mesh(_normal_from_pitch_compass(10.0, 180.0), 3.0)
verts, faces = _combine(close_a, close_b)
groups = d._roof_top_planes(verts, faces)
check("5° Normalenunterschied (< 12°) -> 1 zusammengefasste Gruppe", len(groups) == 1)
check("zusammengefasste Fläche = 9+9 = 18.0", groups and abs(groups[0]["area"] - 18.0) < 1e-6)

# Kontrollfall: 20° auseinander (> 12°) -> dürfen NICHT zusammengefasst werden
# (Regressionsschutz gegen zu HOCH gewählten Schwellwert).
far_a = _rect_mesh(_normal_from_pitch_compass(5.0, 180.0), 3.0)
far_b = _rect_mesh(_normal_from_pitch_compass(25.0, 180.0), 3.0)
verts, faces = _combine(far_a, far_b)
groups = d._roof_top_planes(verts, faces)
check("20° Normalenunterschied (> 12°) -> 2 getrennte Gruppen", len(groups) == 2)

# ---------------------------------------------------------------------------
# Feature 4: End-to-End-Import AC20-FZK-Haus.ifc
# ---------------------------------------------------------------------------
print("=== Feature 4: End-to-End-Import (AC20-FZK-Haus.ifc) ===")
ifc_path = Path.home() / "Downloads" / "AC20-FZK-Haus.ifc"
if not ifc_path.exists():
    print(f"  (übersprungen — Testdatei nicht gefunden: {ifc_path})")
else:
    with open(ifc_path, "rb") as f:
        file_bytes = f.read()
    result = d.extract_all(file_bytes)
    check("Import ohne Exception durchgelaufen", isinstance(result, dict))
    check("building_name plausibel", bool(result.get("building_name")))
    check("storeys > 0", (result.get("storeys") or 0) > 0)
    check("bgf > 0", (result.get("bgf") or 0) > 0)

    env = result["envelope"]
    roof_elements = env["roof_elements"]
    check("genau 2 Dach-Elemente (Satteldach als 2 Slabs)", len(roof_elements) == 2)
    for i, elem in enumerate(sorted(roof_elements, key=lambda e: e["name"])):
        check(f"{elem['name']}: Fläche ≈ 82.56 m² (±0.5)", abs(elem["area"] - 82.56) < 0.5)
        check(f"{elem['name']}: pitch ≈ 30° (±1°)", elem["pitch_deg"] is not None and abs(elem["pitch_deg"] - 30.0) < 1.0)
    if len(roof_elements) == 2:
        az1, az2 = roof_elements[0]["azimuth_deg"], roof_elements[1]["azimuth_deg"]
        diff = abs(abs(az1 - az2) - 180.0) if (az1 is not None and az2 is not None) else None
        check("Dachflächen gegenläufig ausgerichtet (Δazimuth ≈ 180°, ±2°)",
              diff is not None and diff < 2.0)
        both = {round(az1), round(az2)} if az1 is not None and az2 is not None else set()
        check("Azimute ≈ 130°/-50° (TrueNorth-Offset korrekt einbezogen, ±2°)",
              az1 is not None and az2 is not None
              and any(abs(az1 - t) < 2.0 for t in (130.0, -50.0))
              and any(abs(az2 - t) < 2.0 for t in (130.0, -50.0)))

    footprint = env["footprint"]
    rooms = env["rooms"]
    check("footprint nicht leer", len(footprint) > 0)
    check("footprint-Punkte haben x/y", all(("x" in p and "y" in p) for p in footprint))
    check("rooms nicht leer", len(rooms) > 0)
    check("room-Punkte haben x/y", all(("x" in p and "y" in p) for r in rooms for p in r["pts"]))

    geo = result["geometry"]
    check("geometry.meshes nicht leer", len(geo["meshes"]) > 0)
    check("jedes Mesh hat vertices/faces/type/id",
          all({"vertices", "faces", "type", "id"} <= set(m.keys()) for m in geo["meshes"]))

    wall_sum = sum(env["walls"].values())
    window_sum = sum(env["windows"].values())
    door_sum = sum(v["area_per_unit"] * v["count"] for v in env["doors"].values())
    check("Wandflächen-Summe > 0", wall_sum > 0)
    check("Fensterflächen-Summe > 0", window_sum > 0)
    check("Türflächen-Summe > 0", door_sum > 0)

    roof_area_sum = sum(e["area"] for e in roof_elements)
    check("roof_area = Summe der roof_elements-Flächen (keine Doppelzählung/verlorene Fläche)",
          abs(env["roof_area"] - roof_area_sum) < 0.1)

print()
print("ALLE TESTS BESTANDEN ✅" if ok else "TESTS FEHLGESCHLAGEN ❌")
sys.exit(0 if ok else 1)
