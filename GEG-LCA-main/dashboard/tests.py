"""
Unit-Tests für die Energiebilanz-Engine (services.din_v18599).
"""

from django.test import TestCase

from dashboard.services.din_v18599 import (
    calculate_envelope_profile,
    calculate_system_profile,
    calculate_reference_building,
    _gain_utilization_factor,
)


def _sample_building(**overrides):
    """Plausibles EFH (BGF 150, mittelschwerer Massivbau, GEG-Referenz-U-Werte)."""
    base = {
        "bgf": 150.0,
        "room_height": 2.7,
        "air_change_rate": 0.5,
        "heat_recovery": 0.0,
        "thermal_bridge_factor": 0.10,
        "internal_gains_density": 3.0,
        "thermal_mass_class": "medium",
        "climate_location": "potsdam",
        "north_area": 30.0, "north_u": 0.28,
        "south_area": 30.0, "south_u": 0.28,
        "east_area":  30.0, "east_u":  0.28,
        "west_area":  30.0, "west_u":  0.28,
        "roof_area": 90.0, "roof_u": 0.20,
        "floor_area": 90.0, "floor_u": 0.35,
        "window_north_area": 2.0,
        "window_south_area": 8.0,
        "window_east_area":  3.0,
        "window_west_area":  3.0,
        "window_u": 1.30,
        "g_value": 0.60,
        "door_south_count": 1, "door_area_per_unit": 2.0, "door_u": 1.80,
    }
    base.update(overrides)
    return base


class EnvelopeMonthlyBalanceTests(TestCase):

    def test_basic_calculation_succeeds(self):
        result = calculate_envelope_profile(_sample_building())
        self.assertTrue(result["ok"], msg=result.get("errors"))
        self.assertEqual(len(result["monthly_balance"]), 12)

    def test_realistic_range(self):
        result = calculate_envelope_profile(_sample_building())
        spec = result["specific_heat_demand"]
        self.assertGreater(spec, 15, f"spez. HWB zu niedrig: {spec}")
        self.assertLess(spec, 100, f"spez. HWB zu hoch: {spec}")

    def test_winter_higher_than_summer_losses(self):
        result = calculate_envelope_profile(_sample_building())
        jan = result["monthly_balance"][0]
        jul = result["monthly_balance"][6]
        self.assertGreater(jan["losses_kwh"], jul["losses_kwh"])

    def test_no_heating_in_summer(self):
        result = calculate_envelope_profile(_sample_building())
        for m_idx in (6, 7):
            self.assertEqual(result["monthly_balance"][m_idx]["heat_demand_kwh"], 0)

    def test_cold_location_higher_demand(self):
        warm = calculate_envelope_profile(_sample_building(climate_location="freiburg"))
        cold = calculate_envelope_profile(_sample_building(climate_location="garmisch"))
        warm_total = sum(m["heat_demand_kwh"] for m in warm["monthly_balance"])
        cold_total = sum(m["heat_demand_kwh"] for m in cold["monthly_balance"])
        self.assertGreater(cold_total, warm_total)

    def test_heat_recovery_reduces_demand(self):
        without = calculate_envelope_profile(_sample_building(heat_recovery=0.0))
        with_wrg = calculate_envelope_profile(_sample_building(heat_recovery=0.8))
        without_total = sum(m["heat_demand_kwh"] for m in without["monthly_balance"])
        with_wrg_total = sum(m["heat_demand_kwh"] for m in with_wrg["monthly_balance"])
        self.assertGreater(without_total, with_wrg_total)

    def test_invalid_bgf_returns_error(self):
        result = calculate_envelope_profile(_sample_building(bgf=0))
        self.assertFalse(result["ok"])


class GainUtilizationFactorTests(TestCase):

    def test_low_gamma_full_use(self):
        self.assertGreater(_gain_utilization_factor(0.1, 100), 0.95)

    def test_high_gamma_low_use(self):
        self.assertLess(_gain_utilization_factor(5.0, 100), 0.3)

    def test_heavier_mass_higher_eta(self):
        self.assertGreater(
            _gain_utilization_factor(1.0, 200),
            _gain_utilization_factor(1.0, 20),
        )


class SystemProfileTests(TestCase):

    def test_gas_legacy_fields_present(self):
        r = calculate_system_profile({
            "heat_demand_net": 8000, "bgf": 150,
            "heating_system": "gas", "efficiency": 0.92,
        })
        self.assertTrue(r["ok"])
        for k in ("primary_energy", "specific_primary_energy", "total_end_energy",
                  "system_label", "co2_emissions", "non_renewable_primary_energy"):
            self.assertIn(k, r)

    def test_heatpump_uses_electricity_factor(self):
        r = calculate_system_profile({
            "heat_demand_net": 8000, "bgf": 150,
            "heating_system": "heatpump", "cop": 3.5,
        })
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["primary_energy"] / r["total_end_energy"], 1.8, delta=0.05)

    def test_pv_reduces_primary_energy(self):
        without = calculate_system_profile({
            "heat_demand_net": 8000, "bgf": 150,
            "heating_system": "heatpump", "cop": 3.5,
        })
        with_pv = calculate_system_profile({
            "heat_demand_net": 8000, "bgf": 150,
            "heating_system": "heatpump", "cop": 3.5,
            "pv_self_consumption_kwh": 2000,
        })
        self.assertLess(with_pv["primary_energy"], without["primary_energy"])
        self.assertLess(with_pv["co2_emissions"], without["co2_emissions"])

    def test_invalid_system_returns_error(self):
        r = calculate_system_profile({
            "heat_demand_net": 8000, "bgf": 150,
            "heating_system": "kohlekraft", "efficiency": 0.9,
        })
        self.assertFalse(r["ok"])


class GEGReferenceBuildingTests(TestCase):

    def test_reference_compliant_at_reference_u_values(self):
        ref = calculate_reference_building(_sample_building())
        self.assertTrue(ref["ok"])
        self.assertAlmostEqual(ref["ratio_actual_to_reference"], 1.0, delta=0.05)

    def test_bad_envelope_fails_geg(self):
        bad = _sample_building(
            north_u=1.0, south_u=1.0, east_u=1.0, west_u=1.0,
            roof_u=0.8, floor_u=0.8, window_u=2.8,
        )
        ref = calculate_reference_building(bad)
        self.assertTrue(ref["ok"])
        self.assertFalse(ref["geg_compliant_envelope"])
        self.assertGreater(ref["ratio_actual_to_reference"], 1.0)
