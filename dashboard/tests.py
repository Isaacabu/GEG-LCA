"""
Regressionstests für die drei normativen Rechenkerne (DIN 4108, DIN V 18599-2,
DIN V 18599-5/-6/-8). Ersetzt das bisher leere tests.py.

Herkunft der Werte:
- DIN 4108: 1:1 aus scripts/verify_din4108.py übernommen (dort bereits gegen
  Norm-Tabellen/-Gleichungen handgerechnet, alle Checks bestanden ✅).
- DIN V 18599-2 (Hülle): Referenz-EFH aus scripts/verify_din18599.py.
  H_T = 126,22 W/K ist eine unabhängige Handrechnung (siehe Docstring dort:
  88·0,24 + 100·0,20 + 100·0,175 + 30·1,10 + 2·1,30 + 32,0). Die übrigen Werte
  (H_V, Q_h,b,a, spezifisch) sind zum Zeitpunkt dieses Tickets als
  Regressions-Baseline gepinnt (deterministischer Output des aktuellen Codes),
  NICHT unabhängig gegen eine zweite Quelle nachgerechnet.
- DIN V 18599-5/-6/-8 (Anlage): Referenz-EFH aus scripts/verify_din18599_anlage.py.
  Q_w,b = max(16,5−7,5; 8,5)·150·0,98 = 1.323 kWh/a ist laut
  docs/DIN18599_Umsetzung.md §13 eine unabhängige Handrechnung. Primärenergie/
  CO₂ werden hier nur auf Selbstkonsistenz geprüft (Formel fuel·F_P + strom·F_P,
  mit denselben F_PRIMARY/F_CO2-Konstanten aus dem Modul) — das bestätigt, dass
  der Code intern tut was er behauptet, ist aber KEIN unabhängiger Norm-Oracle
  für die Endenergie-/Primärenergie-Endwerte. Größte verbleibende Lücke, siehe
  Analysebericht: ein unabhängiger Oracle für die volle Anlagenkette (Endenergie/
  Primärenergie/CO₂) fehlt noch.
"""
from django.test import SimpleTestCase

from dashboard.services.din4108 import (
    berechne_sommerlicher_waermeschutz,
    berechne_tauwasser_glaser,
    p_sat,
    pruefe_luftdichtheit,
    pruefe_mindestwaermeschutz,
    waermebruecken_zuschlag,
)
from dashboard.services.din18599 import calculate_heat_demand
from dashboard.services.din18599_anlage import F_CO2, F_PRIMARY, calculate_system_din

# Referenz-EFH (150 m², GEG-nah) — identisch mit scripts/verify_din18599.py
# und scripts/verify_din18599_anlage.py. Handrechnung H_T siehe Docstring dort.
REFERENZ_EFH_ENVELOPE = {
    "bgf": 150, "room_height": 2.6, "building_type": "wohngebaeude",
    "building_type_variant": "EFH",
    "north_area": 30, "north_u": 0.24,
    "south_area": 30, "south_u": 0.24,
    "east_area": 30, "east_u": 0.24,
    "west_area": 30, "west_u": 0.24,
    "roof_area": 100, "roof_u": 0.20,
    "floor_area": 100, "floor_u": 0.175,
    "window_north_area": 5, "window_south_area": 15,
    "window_east_area": 5, "window_west_area": 5,
    "window_u": 1.10, "g_value": 0.60,
    "door_south_count": 1, "door_area_per_unit": 2.0, "door_u": 1.30,
}


class Din4108MindestwaermeschutzTests(SimpleTestCase):
    """Tab. 3 Mindestwärmeschutz. Werte aus verify_din4108.py Feature 1."""

    def setUp(self):
        self.r = pruefe_mindestwaermeschutz({"bauteile": [
            {"name": "Außenwand WDVS", "typ": "aussenwand", "u": 0.20},
            {"name": "Kellerdecke dünn", "typ": "decke_unten_keller", "R": 0.5},
            {"name": "Holzständerwand", "typ": "aussenwand", "R": 1.3, "flaechenmasse": 60},
        ]})

    def test_rechnung_ok(self):
        self.assertTrue(self.r["ok"])

    def test_aussenwand_erfuellt(self):
        self.assertTrue(self.r["bauteile"][0]["erfuellt"])

    def test_kellerdecke_nicht_erfuellt(self):
        self.assertFalse(self.r["bauteile"][1]["erfuellt"])

    def test_leichtbauteil_r_min_175(self):
        self.assertAlmostEqual(self.r["bauteile"][2]["r_min"], 1.75, places=6)

    def test_leichtbauteil_nicht_erfuellt(self):
        self.assertFalse(self.r["bauteile"][2]["erfuellt"])

    def test_gesamt_nicht_erfuellt(self):
        self.assertFalse(self.r["alle_erfuellt"])


class Din4108SommerlicherWaermeschutzTests(SimpleTestCase):
    """§8.4 Sonneneintragskennwert. Werte aus verify_din4108.py Feature 2."""

    def test_mit_sonnenschutz_erfuellt(self):
        r = berechne_sommerlicher_waermeschutz({
            "a_g": 20.0, "nutzung": "wohn", "klimaregion": "B", "bauart": "schwer",
            "nachtlueftung": "erhoeht",
            "fenster": [{"flaeche": 4.0, "orientierung": "south", "neigung": 90, "g": 0.6, "fc": 0.25}],
        })
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["anteile"]["S1_grund"], 0.113, places=6)
        self.assertAlmostEqual(r["f_wg_prozent"], 20.0, places=6)
        self.assertAlmostEqual(r["anteile"]["S2_fensteranteil"], 0.060 - 0.231 * 0.20, places=4)
        self.assertAlmostEqual(r["s_vorh"], 0.03, places=6)
        self.assertTrue(r["erfuellt"])

    def test_ohne_sonnenschutz_leicht_region_c_nicht_erfuellt(self):
        r = berechne_sommerlicher_waermeschutz({
            "a_g": 20.0, "nutzung": "wohn", "klimaregion": "C", "bauart": "leicht",
            "nachtlueftung": "ohne",
            "fenster": [{"flaeche": 5.0, "orientierung": "south", "neigung": 90, "g": 0.6, "fc": 1.0}],
        })
        self.assertFalse(r["erfuellt"])


class Din4108TauwasserGlaserTests(SimpleTestCase):
    """Anhang A Glaser-Verfahren. Werte aus verify_din4108.py Feature 3."""

    def test_p_sat_stuetzwerte_gegen_tabelle_c1(self):
        self.assertAlmostEqual(p_sat(20), 2337, delta=3)
        self.assertAlmostEqual(p_sat(-5), 401, delta=3)
        self.assertAlmostEqual(p_sat(0), 611, delta=2)

    def test_diffusionsoffene_aussendaemmung_zulaessig(self):
        r = berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
            {"name": "Gipsputz innen", "d": 0.015, "lambda": 0.51, "mu": 10},
            {"name": "Stahlbeton", "d": 0.18, "lambda": 2.3, "mu": 130},
            {"name": "Mineralwolle", "d": 0.16, "lambda": 0.035, "mu": 1},
            {"name": "Kalkzementputz außen", "d": 0.02, "lambda": 1.0, "mu": 25},
        ]})
        self.assertTrue(r["ok"])
        self.assertTrue(0.17 < r["u_wert"] < 0.22)
        self.assertTrue(r["erfuellt"])

    def test_innendaemmung_mit_sperre_aussen_erkennt_tauwasser(self):
        r = berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
            {"name": "Gipskarton", "d": 0.0125, "lambda": 0.25, "mu": 8},
            {"name": "Mineralwolle innen", "d": 0.10, "lambda": 0.035, "mu": 1},
            {"name": "Stahlbeton", "d": 0.20, "lambda": 2.3, "mu": 130},
            {"name": "Bitumenbahn außen", "d": 0.005, "lambda": 0.17, "mu": 20000},
        ]})
        self.assertTrue(r["tauwasser"])
        self.assertGreater(r["mc_total"], 0)
        # Ohne Materialschlüssel (manuelle Schicht) → konservativ kapillar, Grenze 1,0
        self.assertTrue(all(abs(e["mc_max"] - 1.0) < 1e-9 for e in r["tauebenen"]))

    def test_tauebene_an_bitumenbahn_hat_grenze_05(self):
        r = berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
            {"name": "Gipskarton", "material": "gipskarton", "d": 0.0125, "lambda": 0.25, "mu": 8},
            {"name": "Mineralwolle innen", "material": "mineralwolle", "d": 0.10, "lambda": 0.035, "mu": 1},
            {"name": "Stahlbeton", "material": "stahlbeton", "d": 0.20, "lambda": 2.3, "mu": 130},
            {"name": "Bitumenbahn außen", "material": "bitumenbahn", "d": 0.005, "lambda": 0.17, "mu": 20000},
        ]})
        self.assertTrue(any(abs(e["mc_max"] - 0.5) < 1e-9 for e in r["tauebenen"]))
        self.assertTrue(
            all(e["mc"] <= e["mc_max"] + 1e-9 for e in r["tauebenen"]) or r["erfuellt"] is False
        )

    def test_holzwerkstoff_an_tauebene_warnt_und_ist_gelb_oder_rot(self):
        r = berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
            {"name": "Gipskarton", "material": "gipskarton", "d": 0.0125, "lambda": 0.25, "mu": 8},
            {"name": "Mineralwolle", "material": "mineralwolle", "d": 0.16, "lambda": 0.035, "mu": 1},
            {"name": "OSB außen", "material": "osb", "d": 0.015, "lambda": 0.13, "mu": 50},
        ]})
        self.assertTrue(r["tauwasser"])
        self.assertGreater(len(r["warnungen"]), 0)
        self.assertIn(r["rating_color"], ("yellow", "red"))

    def test_gelb_pfad_zulaessig_trotz_tauwasser_mit_holzwarnung(self):
        r = berechne_tauwasser_glaser({"bauteil_typ": "wand", "schichten": [
            {"name": "Gipskarton", "material": "gipskarton", "d": 0.0125, "lambda": 0.25, "mu": 8},
            {"name": "Dampfbremse sd2", "material": "dampfbremse_var", "d": 0.0005, "lambda": 0.5, "mu": 4000},
            {"name": "Mineralwolle", "material": "mineralwolle", "d": 0.16, "lambda": 0.035, "mu": 1},
            {"name": "OSB außen", "material": "osb", "d": 0.015, "lambda": 0.13, "mu": 50},
        ]})
        self.assertTrue(r["tauwasser"])
        self.assertTrue(r["erfuellt"])
        self.assertEqual(r["rating_color"], "yellow")
        self.assertEqual(len(r["warnungen"]), 1)
        self.assertTrue(all(e["mc"] <= e["mc_max"] + 1e-9 for e in r["tauebenen"]))
        self.assertTrue(any(abs(e["mc_max"] - 0.5) < 1e-9 for e in r["tauebenen"]))


class Din4108WaermebrueckenLuftdichtheitTests(SimpleTestCase):
    """Bbl. 2 ΔU_WB + Teil 7 Luftdichtheit. Werte aus verify_din4108.py Feature 4."""

    def test_delta_u_wb_kategorien(self):
        self.assertAlmostEqual(waermebruecken_zuschlag("kat_a")["delta_u_wb"], 0.05, places=9)
        self.assertAlmostEqual(waermebruecken_zuschlag("kat_b")["delta_u_wb"], 0.03, places=9)
        self.assertAlmostEqual(waermebruecken_zuschlag("keine")["delta_u_wb"], 0.10, places=9)

    def test_n50_grenzwerte_mit_und_ohne_rlt(self):
        self.assertTrue(pruefe_luftdichtheit({"n50": 2.5, "mit_rlt": False})["n50_erfuellt"])
        self.assertFalse(pruefe_luftdichtheit({"n50": 2.5, "mit_rlt": True})["n50_erfuellt"])


class Din18599HeatDemandTests(SimpleTestCase):
    """
    DIN V 18599-2 Monatsbilanz am Referenz-EFH (scripts/verify_din18599.py).
    H_T ist unabhängig handgerechnet (Docstring dort); die übrigen Werte sind
    Regressions-Baseline des aktuellen Codes.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.r = calculate_heat_demand(REFERENZ_EFH_ENVELOPE)

    def test_rechnung_ok(self):
        self.assertTrue(self.r["ok"])

    def test_h_transmission_gegen_handrechnung(self):
        # 88*0,24 + 100*0,20 + 100*0,175 + 30*1,10 + 2*1,30 + 32,0 = 126,22 W/K
        self.assertAlmostEqual(self.r["h_transmission"], 126.22, places=2)

    def test_h_ventilation_regression(self):
        self.assertAlmostEqual(self.r["h_ventilation"], 66.30, delta=0.05)

    def test_heizwaermebedarf_regression(self):
        self.assertAlmostEqual(self.r["adjusted_heat_demand_kwh"], 10188.0, delta=1.0)
        self.assertAlmostEqual(self.r["specific_heat_demand"], 67.92, delta=0.05)

    def test_komponentensumme_stimmt_mit_waermesenke_ueberein(self):
        hb = self.r["heat_balance"]
        comp_sum = sum(hb["transmission"].values()) + hb["ventilation_kwh"]
        self.assertAlmostEqual(comp_sum, hb["sinks_total_kwh"], delta=1.0)

    def test_plausibilitaet_efh_geg_nah(self):
        self.assertTrue(20 <= self.r["specific_heat_demand"] <= 100)


class Din18599AnlageTests(SimpleTestCase):
    """
    DIN V 18599-5/-6/-8 Anlagentechnik am Referenz-EFH
    (scripts/verify_din18599_anlage.py).

    Q_w,b ist unabhängig handgerechnet (docs/DIN18599_Umsetzung.md §13).
    Primärenergie/CO2 werden nur auf Selbstkonsistenz mit F_PRIMARY/F_CO2
    geprüft — KEIN unabhängiger Norm-Oracle, siehe Modul-Docstring oben.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = {
            "bgf": 150, "room_height": 2.6, "building_type": "wohngebaeude",
            "building_type_variant": "EFH", "envelope": REFERENZ_EFH_ENVELOPE,
            "ventilation_system_type": "none",
        }
        cls.gas = calculate_system_din({**base, "heating_system": "gas"})
        cls.wp = calculate_system_din({**base, "heating_system": "heatpump", "cop": 3.5})
        cls.wrg = calculate_system_din({
            **base, "heating_system": "heatpump", "cop": 3.5,
            "ventilation_system_type": "balanced_hr",
            "ventilation_heat_recovery_eff": 0.8, "ventilation_fan_type": "dc",
        })

    def test_rechnung_ok(self):
        self.assertTrue(self.gas["ok"])
        self.assertTrue(self.wp["ok"])
        self.assertTrue(self.wrg["ok"])

    def test_q_w_b_gegen_handrechnung(self):
        # Q_w,b = max(16,5-7,5; 8,5) * 150 * 0,98 = 1.323 kWh/a
        self.assertAlmostEqual(self.gas["din"]["q_w_b"], 1323, delta=1)

    def test_primaerenergie_selbstkonsistent_mit_geg_faktoren(self):
        d = self.gas
        fuel = d["heating_end_energy"] + d["hotwater_end_energy"]
        elec = d["auxiliary_electricity"]
        erwartet = fuel * F_PRIMARY["gas"] + elec * F_PRIMARY["electricity"]
        self.assertAlmostEqual(d["primary_energy"], erwartet, delta=1.0)

    def test_co2_selbstkonsistent_mit_geg_faktoren(self):
        d = self.gas
        fuel = d["heating_end_energy"] + d["hotwater_end_energy"]
        elec = d["auxiliary_electricity"]
        erwartet = fuel * F_CO2["gas"] + elec * F_CO2["electricity"]
        self.assertAlmostEqual(d["co2_emissions"], erwartet, delta=1.0)

    def test_waermepumpe_jaz_plausibel_fuer_fussbodenheizung(self):
        jaz = self.wp["din"]["jaz"]
        self.assertTrue(2.8 <= jaz <= 4.8, f"JAZ {jaz} außerhalb 2.8-4.8")

    def test_waermerueckgewinnung_senkt_heizwaermebedarf(self):
        diff = self.wp["adjusted_heat_demand_net"] - self.wrg["adjusted_heat_demand_net"]
        self.assertGreater(diff, 500)

    def test_gas_endenergie_spezifisch_plausibel(self):
        spez = self.gas["total_end_energy"] / 150
        self.assertTrue(60 <= spez <= 130, f"{spez} kWh/m²a außerhalb Plausibilitätsband")
