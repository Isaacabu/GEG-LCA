"""
Zentrale Konstanten für alle Berechnungen.
Magic Numbers sollten hier verwaltet werden (DRY-Prinzip, einfach anpassbar).
"""

# ===== SOLARFAKTOREN (in kWh/m² für verschiedene Orientierungen) =====
SOLAR_FACTORS = {
    'north': 20,      # Norden: Geringste Solargewinne
    'south': 90,      # Süden: Höchste Solargewinne
    'east': 50,       # Osten: Mittlere Solargewinne (Morgen)
    'west': 50,       # Westen: Mittlere Solargewinne (Nachmittag)
}

# ===== PRIMÄRENERGIEFAKTOREN (nach Energieträger) =====
PRIMARY_ENERGY_FACTORS = {
    'gas': 1.1,       # Erdgas (konventionell)
    'heatpump': 1.8,  # Wärmepumpe (Strom mit deutschem Mix)
    'district': 0.7,  # Fernwärme (effizienter)
    'pellet': 0.2,    # Pellets/Biomasse (erneuerbar)
}

# ===== CO2-EMISSIONSFAKTOREN (kg/kWh) =====
CO2_FACTORS = {
    'gas': 0.24,      # Erdgas
    'heatpump': 0.40, # Wärmepumpe (abhängig von Strommix)
    'district': 0.18, # Fernwärme
    'pellet': 0.04,   # Pellets/Biomasse
}

# ===== HEIZWÄRMEBEDARF BEWERTUNGSGRENZEN (kWh/m²a) =====
RATING_THRESHOLDS = {
    'excellent': 40,   # <= 40 kWh/m²a = sehr gut (grün)
    'medium': 80,      # <= 80 kWh/m²a = mittel (gelb)
    # > 80 = kritisch (rot)
}

# ===== ANLAGENTECHNIK BEWERTUNGSGRENZEN (Primärenergie in kWh/m²a) =====
SYSTEM_RATING_THRESHOLDS = {
    'efficient': 60,    # <= 60 = sehr effizient (grün)
    'medium': 120,      # <= 120 = mittel (gelb)
    # > 120 = verbesserungsbedarf (rot)
}

# ===== STANDARDWERTE FÜR EINGABEN =====
DEFAULT_GRADSTUNDEN = 78000            # Gradstunden pro Jahr (Deutschland)
DEFAULT_G_VALUE = 0.55                 # Solarwärmeverlussfaktor für Fenster
DEFAULT_EFFICIENCY = 0.9               # Standardwirkungsgrad Heizkessel
DEFAULT_COP = 3.5                      # Standard COP für Wärmepumpen
DEFAULT_HOTWATER_DEMAND = 3000         # kWh/a Warmwasser
DEFAULT_AUXILIARY_ELECTRICITY = 1200   # kWh/a Hilfsstrom

# ===== WÄRMEWIDERSTANDSWERTE (nach DIN) =====
DEFAULT_R_SI = 0.13    # Wärmewiderstand innen (m²K/W)
DEFAULT_R_SE = 0.04    # Wärmewiderstand außen (m²K/W)

# ===== LÜFTUNGSPARAMETER =====
VENTILATION_CONSTANT = 0.34            # Konstante für Lüftungswärmeverlust-Berechnung
DEFAULT_AIR_CHANGE_RATE = 0.5          # n = 0,5 h⁻¹ (Luftwechsel pro Stunde)
DEFAULT_ROOM_HEIGHT = 3.0              # m (Standardraumhöhe)

# ===== THERMISCHE BRÜCKEN =====
DEFAULT_THERMAL_BRIDGE_FACTOR = 0.05   # 5% Zuschlag für Wärmebrücken

# ===== INTERNE GEWINNE & BELEGUNG =====
DEFAULT_INTERNAL_GAINS_DENSITY = 2.0   # W/m²
DEFAULT_OCCUPANCY_HOURS = 2500         # h/a
DEFAULT_GAIN_UTILIZATION_FACTOR = 0.75 # Gewinnnutzungsgrad

# ===== PHOTOVOLTAIK =====
DEFAULT_PV_KWP = 8.0                   # Standardanlage: 8 kWp
DEFAULT_SPECIFIC_PV_YIELD = 950.0      # kWh/kWp*a (regional abhängig)
DEFAULT_SELF_CONSUMPTION_RATE = 0.30   # 30% Eigenverbrauch
DEFAULT_ELECTRICITY_PRICE = 0.35       # €/kWh Strompreis
DEFAULT_FEED_IN_TARIFF = 0.08          # €/kWh Einspeisevergütung

# ===== ENERGIEBILANZ =====
DEFAULT_HOUSEHOLD_ELECTRICITY = 2000   # kWh/a Haushaltsstrom
DEFAULT_ELECTRICITY_CO2_FACTOR = 0.40  # kg/kWh (deutscher Strommix)

# ===== GÜLTIGE SYSTEME =====
VALID_HEATING_SYSTEMS = ["gas", "heatpump", "district", "pellet"]

# ===== PLAUSIBILITÄTSPRÜFUNGEN =====
MIN_EFFICIENCY = 0.0                   # Wirkungsgrad Minimum
MAX_EFFICIENCY = 1.2                   # Wirkungsgrad Maximum
MIN_COP = 0.0                          # COP Minimum
MAX_COP = 10.0                         # COP Maximum
MAX_U_VALUE = 5.0                      # Maximaler U-Wert (W/m²K)
MIN_G_VALUE = 0.0                      # g-Wert Minimum
MAX_G_VALUE = 1.0                      # g-Wert Maximum
