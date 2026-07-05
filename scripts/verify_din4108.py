#!/usr/bin/env python
"""Plausibilitäts-/Verifikationsrechnungen für die DIN-4108-Rechenkerne.

Standalone (kein Django nötig): importiert nur dashboard.services.din4108.
Aufruf: python scripts/verify_din4108.py
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# utils relativ importierbar machen (dashboard ist Package)
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
    # utils
    spec = importlib.util.spec_from_file_location("dashboard.utils", base / "utils.py")
    utils = importlib.util.module_from_spec(spec)
    sys.modules["dashboard.utils"] = utils
    spec.loader.exec_module(utils)
    # din4108
    spec = importlib.util.spec_from_file_location("dashboard.services.din4108",
                                                  base / "services" / "din4108.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["dashboard.services.din4108"] = mod
    spec.loader.exec_module(mod)
    return mod


d = _load()
ok = True


def check(name, cond):
    global ok
    print(("  ✓ " if cond else "  ✗ ") + name)
    ok = ok and cond


print("=== Feature 1: Mindestwärmeschutz (Tab. 3) ===")
r = d.pruefe_mindestwaermeschutz({"bauteile": [
    {"name": "Außenwand WDVS", "typ": "aussenwand", "u": 0.20},   # R≈4.8 >> 1.2
    {"name": "Kellerdecke dünn", "typ": "decke_unten_keller", "R": 0.5},  # < 0.90
    {"name": "Holzständerwand", "typ": "aussenwand", "R": 1.3, "flaechenmasse": 60},  # m'<100 → 1.75 → fail
]})
check("Rechnung ok", r["ok"])
check("Außenwand erfüllt", r["bauteile"][0]["erfuellt"] is True)
check("Kellerdecke nicht erfüllt (R0.5<0.9)", r["bauteile"][1]["erfuellt"] is False)
check("Leichtbauteil m'<100 → R_min 1.75", abs(r["bauteile"][2]["r_min"] - 1.75) < 1e-6)
check("Leichtbauteil nicht erfüllt", r["bauteile"][2]["erfuellt"] is False)
check("Gesamt nicht erfüllt", r["alle_erfuellt"] is False)

print("=== Feature 2: Sommerlicher Wärmeschutz (§8.4) ===")
# Wohn-EFH, Region B, schwere Bauart, erhöhte Nachtlüftung, Südfenster mit außenliegendem Sonnenschutz
r = d.berechne_sommerlicher_waermeschutz({
    "a_g": 20.0, "nutzung": "wohn", "klimaregion": "B", "bauart": "schwer",
    "nachtlueftung": "erhoeht",
    "fenster": [{"flaeche": 4.0, "orientierung": "south", "neigung": 90, "g": 0.6, "fc": 0.25}],
})
check("Rechnung ok", r["ok"])
# f_wg = 4/20 = 0.20; S1(erhoeht,schwer,wohn,B)=0.113; S2=0.060-0.231*0.20=0.0138
check("S1 korrekt (0.113)", abs(r["anteile"]["S1_grund"] - 0.113) < 1e-6)
check("f_wg = 20%", abs(r["f_wg_prozent"] - 20.0) < 1e-6)
check("S2 korrekt", abs(r["anteile"]["S2_fensteranteil"] - (0.060 - 0.231 * 0.20)) < 1e-4)
# S_vorh = 4*0.6*0.25/20 = 0.03; S_zul = 0.113+0.0138 = 0.1268 → erfüllt
check("S_vorh = 0.03", abs(r["s_vorh"] - 0.03) < 1e-6)
check("erfüllt (Sonnenschutz wirkt)", r["erfuellt"] is True)
# Gegenprobe ohne Sonnenschutz: fc=1 → S_vorh=0.12, leicht, ohne Nachtlüftung → fail
r2 = d.berechne_sommerlicher_waermeschutz({
    "a_g": 20.0, "nutzung": "wohn", "klimaregion": "C", "bauart": "leicht",
    "nachtlueftung": "ohne",
    "fenster": [{"flaeche": 5.0, "orientierung": "south", "neigung": 90, "g": 0.6, "fc": 1.0}],
})
check("ohne Sonnenschutz, leicht, Region C → nicht erfüllt", r2["erfuellt"] is False)

print("=== Feature 3: Tauwasser / Glaser (Anhang A) ===")
# p_sat-Stützwerte gegen Tabelle C.1
check("p_sat(20) ≈ 2337", abs(d.p_sat(20) - 2337) < 3)
check("p_sat(-5) ≈ 401", abs(d.p_sat(-5) - 401) < 3)
check("p_sat(0) ≈ 611", abs(d.p_sat(0) - 611) < 2)
# Gut gedämmte Außenwand mit Außendämmung (diffusionsoffen außen) → kein/wenig Tauwasser
r = d.berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
    {"name": "Gipsputz innen", "d": 0.015, "lambda": 0.51, "mu": 10},
    {"name": "Stahlbeton", "d": 0.18, "lambda": 2.3, "mu": 130},
    {"name": "Mineralwolle", "d": 0.16, "lambda": 0.035, "mu": 1},
    {"name": "Kalkzementputz außen", "d": 0.02, "lambda": 1.0, "mu": 25},
]})
check("Rechnung ok", r["ok"])
check("U-Wert plausibel (~0.19)", 0.17 < r["u_wert"] < 0.22)
check("diffusionsoffene Wand zulässig", r["erfuellt"] is True)
# Problemfall: Innendämmung mit Dampfsperre außen (Bitumen) → Tauwasser
r2 = d.berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
    {"name": "Gipskarton", "d": 0.0125, "lambda": 0.25, "mu": 8},
    {"name": "Mineralwolle innen", "d": 0.10, "lambda": 0.035, "mu": 1},
    {"name": "Stahlbeton", "d": 0.20, "lambda": 2.3, "mu": 130},
    {"name": "Bitumenbahn außen", "d": 0.005, "lambda": 0.17, "mu": 20000},
]})
check("Innendämmung+Sperre außen → Tauwasser erkannt", r2["tauwasser"] is True)
check("Tauwassermasse > 0", r2["mc_total"] > 0)
# §5.2.2 strengere Grenze: Tauebene an nicht kapillar saugender Schicht → mc_max 0,5.
# Materialschlüssel steuern die Flags (bitumenbahn/mineralwolle nicht saugend).
r3 = d.berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
    {"name": "Gipskarton", "material": "gipskarton", "d": 0.0125, "lambda": 0.25, "mu": 8},
    {"name": "Mineralwolle innen", "material": "mineralwolle", "d": 0.10, "lambda": 0.035, "mu": 1},
    {"name": "Stahlbeton", "material": "stahlbeton", "d": 0.20, "lambda": 2.3, "mu": 130},
    {"name": "Bitumenbahn außen", "material": "bitumenbahn", "d": 0.005, "lambda": 0.17, "mu": 20000},
]})
check("Tauebene an Bitumenbahn → Grenze 0,5 kg/m²",
      any(abs(e["mc_max"] - 0.5) < 1e-9 for e in r3["tauebenen"]))
check("Ebenen-Grenze fließt in Bewertung ein (mc>mc_max → nicht erfüllt)",
      all(e["mc"] <= e["mc_max"] + 1e-9 for e in r3["tauebenen"]) or r3["erfuellt"] is False)
# Ohne Materialschlüssel (manuelle Schicht) → konservativ kapillar, Grenze 1,0
check("manuelle Schichten → Standardgrenze 1,0",
      all(abs(e["mc_max"] - 1.0) < 1e-9 for e in r2["tauebenen"]))
# Holz-Warnung: Tauwasser an OSB-Grenzfläche → gelb statt grün + Warnhinweis
r4 = d.berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
    {"name": "Gipskarton", "material": "gipskarton", "d": 0.0125, "lambda": 0.25, "mu": 8},
    {"name": "Mineralwolle", "material": "mineralwolle", "d": 0.16, "lambda": 0.035, "mu": 1},
    {"name": "OSB außen", "material": "osb", "d": 0.015, "lambda": 0.13, "mu": 50},
]})
check("Holzwerkstoff an Tauebene → Warnung",
      (not r4["tauwasser"]) or len(r4["warnungen"]) > 0)
check("Holz-Warnung → Ampel gelb (kein falsches Grün)",
      (not r4["tauwasser"]) or (r4["rating_color"] in ("yellow", "red")))
check("Holz-Fall liefert wirklich Tauwasser (Testfall aussagekräftig)", r4["tauwasser"] is True)
# Gelb-Pfad: Holzständerwand mit Dampfbremse sd=2 m → wenig Tauwasser an der OSB,
# verdunstet wieder (zulässig), aber Holz beteiligt → „Erfüllt (mit Vorbehalt)"/gelb
r5 = d.berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
    {"name": "Gipskarton", "material": "gipskarton", "d": 0.0125, "lambda": 0.25, "mu": 8},
    {"name": "Dampfbremse sd2", "material": "dampfbremse_var", "d": 0.0005, "lambda": 0.5, "mu": 4000},
    {"name": "Mineralwolle", "material": "mineralwolle", "d": 0.16, "lambda": 0.035, "mu": 1},
    {"name": "OSB außen", "material": "osb", "d": 0.015, "lambda": 0.13, "mu": 50},
]})
check("Gelb-Pfad: zulässig trotz Tauwasser", r5["tauwasser"] is True and r5["erfuellt"] is True)
check("Gelb-Pfad: Ampel gelb + Holz-Warnung",
      r5["rating_color"] == "yellow" and len(r5["warnungen"]) == 1)
check("Gelb-Pfad: 0,5-Grenze an MW/OSB eingehalten",
      all(e["mc"] <= e["mc_max"] + 1e-9 for e in r5["tauebenen"])
      and any(abs(e["mc_max"] - 0.5) < 1e-9 for e in r5["tauebenen"]))

print("=== Feature 4: Wärmebrücken + Luftdichtheit ===")
check("ΔU_WB Kat. A = 0.05", abs(d.waermebruecken_zuschlag("kat_a")["delta_u_wb"] - 0.05) < 1e-9)
check("ΔU_WB Kat. B = 0.03", abs(d.waermebruecken_zuschlag("kat_b")["delta_u_wb"] - 0.03) < 1e-9)
check("ΔU_WB keiner = 0.10", abs(d.waermebruecken_zuschlag("keine")["delta_u_wb"] - 0.10) < 1e-9)
lr = d.pruefe_luftdichtheit({"n50": 2.5, "mit_rlt": False})
check("n50 2.5 ohne RLT erfüllt (≤3.0)", lr["n50_erfuellt"] is True)
lr2 = d.pruefe_luftdichtheit({"n50": 2.5, "mit_rlt": True})
check("n50 2.5 mit RLT nicht erfüllt (>1.5)", lr2["n50_erfuellt"] is False)

print()
print("ALLE TESTS BESTANDEN ✅" if ok else "TESTS FEHLGESCHLAGEN ❌")
sys.exit(0 if ok else 1)
