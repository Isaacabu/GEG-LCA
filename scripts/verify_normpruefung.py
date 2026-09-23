#!/usr/bin/env python
"""Verifikation der konsolidierten Normprüfung (dashboard/services/normpruefung.py).

Standalone (kein Django nötig): importiert nur dashboard.services.normpruefung.
Aufruf: python scripts/verify_normpruefung.py
"""
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
    spec = importlib.util.spec_from_file_location("dashboard.services.normpruefung",
                                                  base / "services" / "normpruefung.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["dashboard.services.normpruefung"] = mod
    spec.loader.exec_module(mod)
    return mod


d = _load()
ok = True


def check(name, cond):
    global ok
    print(("  ✓ " if cond else "  ✗ ") + name)
    ok = ok and cond


print("=== Feature: leerer Payload ===")
r = d.pruefe_norm_konformitaet({})
check("Rechnung ok", r["ok"])
check("Alle 6 Nachweise fehlen", r["anzahl_fehlend"] == 6)
check("0 geprüft", r["anzahl_geprueft"] == 0)
check("Gesamtfarbe None", r["gesamt_farbe"] is None)

print("=== Feature: nur Heizwärmebedarf (grün) vorhanden ===")
r = d.pruefe_norm_konformitaet({
    "heizwaerme": {"ok": True, "specific_heat_demand": 35.0,
                   "rating_label": "Sehr gut", "rating_color": "green", "rating_message": "..."},
})
check("1 geprüft, 5 fehlen", r["anzahl_geprueft"] == 1 and r["anzahl_fehlend"] == 5)
check("Gesamtfarbe grün", r["gesamt_farbe"] == "green")
check("Wert übernommen", r["pruefungen"][0]["wert"] == 35.0)

print("=== Feature: gemischt grün + gelb + rot → Gesamt rot ===")
r = d.pruefe_norm_konformitaet({
    "heizwaerme": {"ok": True, "specific_heat_demand": 35.0,
                   "rating_label": "Sehr gut", "rating_color": "green", "rating_message": "..."},
    "anlage": {"ok": True, "specific_primary_energy": 90.0,
               "system_label": "Mittel", "system_color": "yellow", "system_message": "..."},
    "mindestwaermeschutz": {"ok": True, "rating_label": "Nicht erfüllt", "rating_color": "red",
                             "rating_message": "..."},
})
check("3 geprüft, 3 fehlen", r["anzahl_geprueft"] == 3 and r["anzahl_fehlend"] == 3)
check("Gesamtfarbe rot (schlechtester Wert zählt)", r["gesamt_farbe"] == "red")
check("Gesamtlabel passend", "nicht erfüllt" in r["gesamt_label"].lower())

print("=== Feature: Teilergebnis mit ok=False zählt als fehlend ===")
r = d.pruefe_norm_konformitaet({
    "tauwasser": {"ok": False, "errors": ["Ungültige Schichten"]},
})
check("Fehlerhaftes Teilergebnis zählt als fehlend", r["anzahl_fehlend"] == 6)

print("\nALLE TESTS BESTANDEN ✅" if ok else "\nFEHLER ❌")
sys.exit(0 if ok else 1)
