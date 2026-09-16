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
from dashboard.services.din18599_multizone import calculate_heat_demand_multizone
from dashboard.services.ifc_import import (
    IfcImportError,
    extract_all,
    extract_basic_data,
    extract_envelope,
    extract_geometry,
)
from dashboard.services.ifc_import import (
    _host_wall,
    _is_external,
    _orientation_from_vector,
    _wall_length_height_dir,
)

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


class Din18599MultizoneTests(SimpleTestCase):
    """
    Mehrzonen-Aggregation (Phase Z2a, services/din18599_multizone.py).

    Konsistenz-Oracle statt unabhängiger Handrechnung: H_T, H_V und die solaren/
    internen Gewinne sind linear in Fläche/BGF, und der Ausnutzungsgrad η hängt nur
    vom (skaleninvarianten) Verhältnis Q_Quelle/Q_Senke ab. Ein gleichförmiges
    Gebäude, exakt in zwei IDENTISCHE Zonen (halbe Flächen/BGF, gleiches Profil)
    geteilt, muss deshalb exakt (bis auf Rundung der Zwischenwerte) dasselbe
    Gesamtergebnis liefern wie die Einzonen-Rechnung fürs ganze Gebäude. Referenz-EFH
    ohne Tür (Türanzahl ist ein Integer, halbiert sich nicht sauber) — sonst
    identisch mit REFERENZ_EFH_ENVELOPE.
    """

    WHOLE = {
        "bgf": 150, "room_height": 2.6, "building_type": "wohngebaeude",
        "building_type_variant": "EFH",
        "north_area": 30, "north_u": 0.24, "south_area": 30, "south_u": 0.24,
        "east_area": 30, "east_u": 0.24, "west_area": 30, "west_u": 0.24,
        "roof_area": 100, "roof_u": 0.20, "floor_area": 100, "floor_u": 0.175,
        "window_north_area": 5, "window_south_area": 15,
        "window_east_area": 5, "window_west_area": 5,
        "window_u": 1.10, "g_value": 0.60,
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.whole = calculate_heat_demand(cls.WHOLE)
        # Nur extensive Größen (Flächen, BGF) halbieren - U-Werte/g-Wert/Raumhöhe sind
        # intensive Größen (pro m²) und bleiben für jede Zone unverändert.
        flaechenfelder = (
            "bgf", "north_area", "south_area", "east_area", "west_area",
            "roof_area", "floor_area",
            "window_north_area", "window_south_area", "window_east_area", "window_west_area",
        )
        half = dict(cls.WHOLE)
        for k in flaechenfelder:
            half[k] = half[k] / 2
        cls.multi = calculate_heat_demand_multizone([dict(half, zone_name="A"), dict(half, zone_name="B")])

    def test_beide_rechnungen_ok(self):
        self.assertTrue(self.whole["ok"])
        self.assertTrue(self.multi["ok"])
        self.assertEqual(self.multi["zone_count"], 2)

    def test_bgf_summe_stimmt(self):
        self.assertAlmostEqual(self.multi["bgf_total"], 150, delta=0.1)

    def test_h_transmission_summe_gleich_ganzes_gebaeude(self):
        self.assertAlmostEqual(self.multi["h_transmission"], self.whole["h_transmission"], delta=0.5)

    def test_h_ventilation_summe_gleich_ganzes_gebaeude(self):
        self.assertAlmostEqual(self.multi["h_ventilation"], self.whole["h_ventilation"], delta=0.5)

    def test_heizwaermebedarf_summe_gleich_ganzes_gebaeude(self):
        # η ist skaleninvariant (hängt nur vom Verhältnis Q_Quelle/Q_Senke ab) →
        # zwei identische halbe Zonen liefern in Summe exakt den Wert des ganzen
        # Gebäudes (bis auf Rundung der Zwischenwerte je Zone).
        self.assertAlmostEqual(
            self.multi["adjusted_heat_demand_kwh"], self.whole["adjusted_heat_demand_kwh"], delta=2.0
        )

    def test_monatswerte_summieren_sich_korrekt(self):
        for m_whole, m_multi in zip(self.whole["monthly"], self.multi["monthly"]):
            self.assertEqual(m_whole["month"], m_multi["month"])
            self.assertAlmostEqual(m_whole["q_heat"], m_multi["q_heat"], delta=1.0)

    def test_leere_zonenliste_liefert_fehler(self):
        r = calculate_heat_demand_multizone([])
        self.assertFalse(r["ok"])

    def test_fehlerhafte_zone_wird_mit_namen_gemeldet(self):
        r = calculate_heat_demand_multizone([{**self.WHOLE, "zone_name": "Kaputt", "bgf": 0}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("Kaputt" in e for e in r["errors"]))


def _build_test_ifc(name="Testgebaeude", n_storeys=2, space_areas=(60.0, 55.0), project_name="Projekt"):
    """Baut ein minimales, gültiges IFC4-Modell in-memory (kein Fixture-File nötig) -
    genug Entitäten, damit extract_basic_data() etwas zum Extrahieren hat. Räume/
    Geschosse müssen für by_type() nicht räumlich verschachtelt sein."""
    import ifcopenshell
    import ifcopenshell.guid as guid

    f = ifcopenshell.file(schema="IFC4")
    f.create_entity("IfcProject", GlobalId=guid.new(), Name=project_name)
    if name is not None:
        f.create_entity("IfcBuilding", GlobalId=guid.new(), Name=name)
    for i in range(n_storeys):
        f.create_entity("IfcBuildingStorey", GlobalId=guid.new(), Name=f"Etage {i}")
    for area in space_areas:
        space = f.create_entity("IfcSpace", GlobalId=guid.new(), Name="Raum")
        q = f.create_entity("IfcQuantityArea", Name="GrossFloorArea", AreaValue=area)
        qset = f.create_entity("IfcElementQuantity", GlobalId=guid.new(), Name="Qto_SpaceBaseQuantities", Quantities=[q])
        f.create_entity("IfcRelDefinesByProperties", GlobalId=guid.new(), RelatedObjects=[space], RelatingPropertyDefinition=qset)
    return f.to_string().encode("utf-8")


class IfcImportTests(SimpleTestCase):
    """
    IFC-Import Phase I1 (services/ifc_import.py) - Grunddaten-Extraktion.
    Test-IFC wird in-memory generiert (_build_test_ifc), keine Norm-Handrechnung
    nötig: die Erwartungswerte sind exakt die Eingaben des selbstgebauten Modells.
    """

    def test_name_geschosse_und_flaeche_korrekt_extrahiert(self):
        r = extract_basic_data(_build_test_ifc(name="Mein Haus", n_storeys=2, space_areas=(60.0, 55.0)))
        self.assertEqual(r["building_name"], "Mein Haus")
        self.assertEqual(r["storeys"], 2)
        self.assertAlmostEqual(r["bgf"], 115.0, places=1)
        self.assertEqual(r["warnings"], [])
        self.assertEqual(r["schema"], "IFC4")

    def test_fehlender_gebaeudename_faellt_auf_projektname_zurueck(self):
        r = extract_basic_data(_build_test_ifc(name=None, project_name="Mein Projekt", n_storeys=1, space_areas=(40.0,)))
        self.assertEqual(r["building_name"], "Mein Projekt")

    def test_gar_kein_name_erzeugt_warnung_und_fallback(self):
        r = extract_basic_data(_build_test_ifc(name=None, project_name=None, n_storeys=1, space_areas=(40.0,)))
        self.assertEqual(r["building_name"], "IFC-Import")
        self.assertTrue(any("name" in w.lower() for w in r["warnings"]))

    def test_keine_geschosse_erzeugt_warnung(self):
        r = extract_basic_data(_build_test_ifc(n_storeys=0, space_areas=(40.0,)))
        self.assertEqual(r["storeys"], 0)
        self.assertTrue(any("geschoss" in w.lower() for w in r["warnings"]))

    def test_keine_flaechen_erzeugt_warnung_und_bgf_none(self):
        r = extract_basic_data(_build_test_ifc(space_areas=()))
        self.assertIsNone(r["bgf"])
        self.assertTrue(any("fläche" in w.lower() for w in r["warnings"]))

    def test_ungueltige_datei_wirft_ifcimporterror(self):
        with self.assertRaises(IfcImportError):
            extract_basic_data(b"das ist keine IFC-Datei")

    def test_leere_datei_wirft_ifcimporterror(self):
        with self.assertRaises(IfcImportError):
            extract_basic_data(b"")


def _build_test_ifc_with_walls(n_walls=2):
    """Baut ein IFC4-Modell mit ECHTER Geometrie (n_walls Wände, je 5×2,7×0,3 m,
    über geometry.create_2pt_wall) - für Tests der Geometrie-Extraktion
    (extract_geometry/extract_all). Jede Box-Wand liefert 8 Vertices/12 Dreiecke."""
    import ifcopenshell
    import ifcopenshell.api.context as context
    import ifcopenshell.api.geometry as geometry
    import ifcopenshell.api.root as root
    import ifcopenshell.api.unit as unit

    f = ifcopenshell.file(schema="IFC4")
    root.create_entity(f, ifc_class="IfcProject", name="Testprojekt")
    unit.assign_unit(f)
    model_ctx = context.add_context(f, context_type="Model")
    body_ctx = context.add_context(
        f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model_ctx
    )
    root.create_entity(f, ifc_class="IfcBuilding", name="Testgebaeude")
    root.create_entity(f, ifc_class="IfcBuildingStorey", name="EG")

    for i in range(n_walls):
        wall = root.create_entity(f, ifc_class="IfcWall", name=f"Wand {i + 1}")
        rep = geometry.create_2pt_wall(
            f, element=wall, context=body_ctx, p1=(0.0, i * 3.0), p2=(5.0, i * 3.0),
            elevation=0.0, height=2.7, thickness=0.3,
        )
        geometry.assign_representation(f, product=wall, representation=rep)

    return f.to_string().encode("utf-8")


class IfcGeometryExtractionTests(SimpleTestCase):
    """IFC-Geometrie-Extraktion für den BIM-Viewer (Phase I2, services/ifc_import.py)."""

    def test_zwei_waende_liefern_zwei_meshes_mit_box_geometrie(self):
        r = extract_geometry(_build_test_ifc_with_walls(2))
        self.assertEqual(r["element_count"], 2)
        self.assertEqual(r["rendered_count"], 2)
        self.assertEqual(len(r["meshes"]), 2)
        for mesh in r["meshes"]:
            self.assertEqual(mesh["type"], "IfcWall")
            # Box-Wand: 8 Eckpunkte (24 Koordinaten), 12 Dreiecke (36 Indizes)
            self.assertEqual(len(mesh["vertices"]), 24)
            self.assertEqual(len(mesh["faces"]), 36)
            self.assertEqual(mesh["color"], 0x2b4a78)

    def test_kein_darstellbares_bauteil_erzeugt_warnung(self):
        r = extract_geometry(_build_test_ifc(n_storeys=1, space_areas=()))
        self.assertEqual(r["rendered_count"], 0)
        self.assertTrue(any("bauteil" in w.lower() for w in r["warnings"]))

    def test_max_elements_begrenzt_und_warnt(self):
        r = extract_geometry(_build_test_ifc_with_walls(3), max_elements=2)
        self.assertEqual(r["element_count"], 3)
        self.assertEqual(r["rendered_count"], 2)
        self.assertTrue(any("nur die ersten" in w.lower() for w in r["warnings"]))

    def test_extract_all_liefert_grunddaten_und_geometrie_zusammen(self):
        r = extract_all(_build_test_ifc_with_walls(1))
        self.assertEqual(r["building_name"], "Testgebaeude")
        self.assertIn("geometry", r)
        self.assertEqual(r["geometry"]["rendered_count"], 1)
        # Geometrie-Warnungen (z.B. fehlende Flächen) landen in derselben Liste wie Grunddaten-Warnungen
        self.assertTrue(any("fläche" in w.lower() for w in r["warnings"]))


class IfcEnvelopeHelperTests(SimpleTestCase):
    """Reine Helferfunktionen der Gebäudehüllen-Extraktion (Phase I3, keine IFC-Datei nötig)."""

    def test_orientation_from_vector_haupthimmelsrichtungen(self):
        # north_offset=0: Modell-Y = Norden (dokumentierte Vereinfachung ohne TrueNorth)
        self.assertEqual(_orientation_from_vector(0, 1, 0), "north")
        self.assertEqual(_orientation_from_vector(1, 0, 0), "east")
        self.assertEqual(_orientation_from_vector(0, -1, 0), "south")
        self.assertEqual(_orientation_from_vector(-1, 0, 0), "west")

    def test_orientation_from_vector_true_north_offset(self):
        # north_offset = atan2(TrueNorth.dx, TrueNorth.dy) im Modell-Koordinatensystem;
        # bearing = raw_angle - offset. TrueNorth bei -90° (Modell-Richtung (-1,0)):
        # Vektor (1,0) hat raw_angle=atan2(1,0)=90°, bearing=90-(-90)=180° -> Süden.
        self.assertEqual(_orientation_from_vector(1, 0, -90), "south")

    def test_wall_length_height_dir_einfache_box(self):
        # Box 5m lang (x), 0.3m dick (y), 2.7m hoch (z) - wie eine create_2pt_wall-Wand.
        # Der Algorithmus sucht das am WEITESTEN entfernte Punktpaar in der XY-Projektion;
        # bei einer dünnen Box ist das die Diagonale (5,0)-(0,0.3), nicht exakt die lange
        # Kante - Differenz bei einer 5m/0,3m-Wand ~0,18 % (5,009 statt 5,0 m), für die
        # Flächenermittlung vernachlässigbar (siehe IfcEnvelopeExtractionTests mit
        # delta-Toleranz). Erwartungswerte hier bewusst exakt auf die Diagonale gerechnet.
        import math
        verts = [
            0, 0, 0,  5, 0, 0,  5, 0.3, 0,  0, 0.3, 0,
            0, 0, 2.7,  5, 0, 2.7,  5, 0.3, 2.7,  0, 0.3, 2.7,
        ]
        length, height, direction, midpoint = _wall_length_height_dir(verts)
        expected_length = math.hypot(5.0, 0.3)
        self.assertAlmostEqual(length, expected_length, places=6)
        self.assertAlmostEqual(height, 2.7, places=6)
        self.assertAlmostEqual(direction[0], 5.0 / expected_length, places=6)
        self.assertAlmostEqual(midpoint[0], 2.5, places=6)

    def test_host_wall_ueber_ifc_beziehungen(self):
        import ifcopenshell
        import ifcopenshell.guid as guid
        f = ifcopenshell.file(schema="IFC4")
        wall = f.create_entity("IfcWall", GlobalId=guid.new(), Name="Wand")
        window = f.create_entity("IfcWindow", GlobalId=guid.new(), Name="Fenster")
        opening = f.create_entity("IfcOpeningElement", GlobalId=guid.new(), Name="Opening")
        f.create_entity("IfcRelVoidsElement", GlobalId=guid.new(), RelatingBuildingElement=wall, RelatedOpeningElement=opening)
        f.create_entity("IfcRelFillsElement", GlobalId=guid.new(), RelatingOpeningElement=opening, RelatedBuildingElement=window)
        self.assertEqual(_host_wall(window), wall)

    def test_host_wall_ohne_beziehung_liefert_none(self):
        import ifcopenshell
        import ifcopenshell.guid as guid
        f = ifcopenshell.file(schema="IFC4")
        window = f.create_entity("IfcWindow", GlobalId=guid.new(), Name="Fenster")
        self.assertIsNone(_host_wall(window))

    def test_is_external_liest_pset_wallcommon(self):
        import ifcopenshell
        import ifcopenshell.guid as guid
        f = ifcopenshell.file(schema="IFC4")
        wall = f.create_entity("IfcWall", GlobalId=guid.new(), Name="Wand")
        nv = f.create_entity("IfcBoolean", True)
        prop = f.create_entity("IfcPropertySingleValue", Name="IsExternal", NominalValue=nv)
        pset = f.create_entity("IfcPropertySet", GlobalId=guid.new(), Name="Pset_WallCommon", HasProperties=[prop])
        f.create_entity("IfcRelDefinesByProperties", GlobalId=guid.new(), RelatedObjects=[wall], RelatingPropertyDefinition=pset)
        self.assertTrue(_is_external(wall))

    def test_is_external_ohne_angabe_liefert_none(self):
        import ifcopenshell
        import ifcopenshell.guid as guid
        f = ifcopenshell.file(schema="IFC4")
        wall = f.create_entity("IfcWall", GlobalId=guid.new(), Name="Wand")
        self.assertIsNone(_is_external(wall))


def _build_test_house_ifc():
    """Rechteck-Haus 6×5 m, Wandhöhe 2,7 m, achsparallel (x=Länge, y=Breite) - für einen
    Ende-zu-Ende-Test der Gebäudehüllen-Extraktion mit VORHERSEHBAREN Orientierungen
    (Süd/Ost/Nord/West bei north_offset=0). Süd-Wand hat ein Fenster (1,2×1,2 m),
    Ost-Wand eine Tür (0,9×2,1 m), beide über echte IFC-Opening-Beziehungen verknüpft.
    Bodenplatte (BASESLAB, 30 m² Qto) und Dach (IfcSlab ROOF, 35 m² Qto) mit
    expliziten Mengenangaben (wie z.B. ArchiCAD sie oft nur für Dach als Slab liefert)."""
    import ifcopenshell
    import ifcopenshell.api.context as context
    import ifcopenshell.api.geometry as geometry
    import ifcopenshell.api.root as root
    import ifcopenshell.api.unit as unit
    import ifcopenshell.guid as guid

    f = ifcopenshell.file(schema="IFC4")
    root.create_entity(f, ifc_class="IfcProject", name="Testprojekt")
    unit.assign_unit(f)
    model_ctx = context.add_context(f, context_type="Model")
    body_ctx = context.add_context(
        f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model_ctx
    )
    root.create_entity(f, ifc_class="IfcBuilding", name="Testhaus")
    root.create_entity(f, ifc_class="IfcBuildingStorey", name="EG")

    W, D, H = 6.0, 5.0, 2.7
    edges = {
        "south": ((0, 0), (W, 0)),
        "east": ((W, 0), (W, D)),
        "north": ((W, D), (0, D)),
        "west": ((0, D), (0, 0)),
    }
    walls = {}
    for key, (p1, p2) in edges.items():
        wall = root.create_entity(f, ifc_class="IfcWall", name=f"Wand {key}")
        rep = geometry.create_2pt_wall(f, element=wall, context=body_ctx, p1=p1, p2=p2, elevation=0.0, height=H, thickness=0.3)
        geometry.assign_representation(f, product=wall, representation=rep)
        walls[key] = wall

    def add_opening(host_wall, ifc_class, name, w, h):
        product = root.create_entity(f, ifc_class=ifc_class, name=name)
        rep = geometry.create_2pt_wall(f, element=product, context=body_ctx, p1=(0, 0), p2=(w, 0), elevation=0.0, height=h, thickness=0.1)
        geometry.assign_representation(f, product=product, representation=rep)
        opening = f.create_entity("IfcOpeningElement", GlobalId=guid.new(), Name="Opening")
        f.create_entity("IfcRelVoidsElement", GlobalId=guid.new(), RelatingBuildingElement=host_wall, RelatedOpeningElement=opening)
        f.create_entity("IfcRelFillsElement", GlobalId=guid.new(), RelatingOpeningElement=opening, RelatedBuildingElement=product)
        return product

    add_opening(walls["south"], "IfcWindow", "Fenster Süd", 1.2, 1.2)
    add_opening(walls["east"], "IfcDoor", "Tür Ost", 0.9, 2.1)

    def add_qto_area(product, qto_name, qty_name, value):
        q = f.create_entity("IfcQuantityArea", Name=qty_name, AreaValue=value)
        qset = f.create_entity("IfcElementQuantity", GlobalId=guid.new(), Name=qto_name, Quantities=[q])
        f.create_entity("IfcRelDefinesByProperties", GlobalId=guid.new(), RelatedObjects=[product], RelatingPropertyDefinition=qset)

    base_slab = root.create_entity(f, ifc_class="IfcSlab", name="Bodenplatte")
    base_slab.PredefinedType = "BASESLAB"
    add_qto_area(base_slab, "Qto_SlabBaseQuantities", "GrossArea", 30.0)

    roof_slab = root.create_entity(f, ifc_class="IfcSlab", name="Dach")
    roof_slab.PredefinedType = "ROOF"
    add_qto_area(roof_slab, "Qto_SlabBaseQuantities", "GrossArea", 35.0)

    return f.to_string().encode("utf-8")


class IfcEnvelopeExtractionTests(SimpleTestCase):
    """Ende-zu-Ende-Test der Gebäudehüllen-Extraktion (Phase I3) an einem synthetischen
    Rechteck-Haus mit bekannten, vorhersehbaren Sollwerten."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.r = extract_envelope(_build_test_house_ifc())

    def test_alle_vier_wandorientierungen_erkannt(self):
        self.assertEqual(set(self.r["walls"].keys()), {"north", "south", "east", "west"})

    def test_wandflaechen_geometrisch_plausibel(self):
        # Süd/Nord-Wände: Länge 6 m × Höhe 2,7 m = 16,2 m²; Ost/West: 5 × 2,7 = 13,5 m²
        self.assertAlmostEqual(self.r["walls"]["south"], 16.2, delta=0.1)
        self.assertAlmostEqual(self.r["walls"]["north"], 16.2, delta=0.1)
        self.assertAlmostEqual(self.r["walls"]["east"], 13.5, delta=0.1)
        self.assertAlmostEqual(self.r["walls"]["west"], 13.5, delta=0.1)

    def test_fenster_der_suedwand_zugeordnet(self):
        self.assertIn("south", self.r["windows"])
        self.assertAlmostEqual(self.r["windows"]["south"], 1.2 * 1.2, delta=0.05)
        self.assertNotIn("east", self.r["windows"])

    def test_tuer_der_ostwand_zugeordnet(self):
        self.assertIn("east", self.r["doors"])
        self.assertEqual(self.r["doors"]["east"]["count"], 1)
        self.assertAlmostEqual(self.r["doors"]["east"]["area_per_unit"], 0.9 * 2.1, delta=0.05)
        self.assertNotIn("south", self.r["doors"])

    def test_dach_und_boden_aus_slab_qto_uebernommen(self):
        self.assertAlmostEqual(self.r["roof_area"], 35.0, places=1)
        self.assertAlmostEqual(self.r["floor_area"], 30.0, places=1)

    def test_geometrischer_aussen_fallback_wird_verwendet_ohne_isexternal(self):
        self.assertTrue(any("geometrisch" in w.lower() for w in self.r["warnings"]))

    def test_leeres_modell_ohne_waende_liefert_warnung(self):
        r = extract_envelope(_build_test_ifc(n_storeys=1, space_areas=()))
        self.assertEqual(r["walls"], {})
        self.assertTrue(any("wände" in w.lower() for w in r["warnings"]))
