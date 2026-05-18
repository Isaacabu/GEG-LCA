"""
Zentrale Konstanten für alle Berechnungen.
Fachgrundlagen:
- DIN V 18599-1/-2/-10 (Energiebilanz, Nutzungsrandbedingungen)
- DIN EN ISO 13790 (Monatsbilanzverfahren, dynamischer Gewinnnutzungsgrad)
- DIN V 4108-6 (Wärmeschutz, Wärmebrücken-Pauschalzuschlag)
- GEG 2024 §22, Anlage 4 (Primärenergiefaktoren)
- UBA / GEMIS 2024 (CO2-Emissionsfaktoren Endenergie)
"""

# =============================================================================
# SOLARSTRAHLUNG (DIN V 18599-10 / TRY Potsdam, vertikale Flächen)
# Jahressummen in kWh/(m²·a)
# =============================================================================
# Heizperioden-Strahlungsangebot je Orientierung (kWh/(m²·Heizperiode))
# vereinfachtes Verfahren – konsistent mit Gradstunden-Methode
SOLAR_FACTORS = {
    'north': 20,
    'south': 90,
    'east':  50,
    'west':  50,
}

# Monatliche Vertikalstrahlung kWh/m² je Monat (Jan..Dez)
MONTHLY_SOLAR_RADIATION = {
    'north':      [11, 17, 28, 38, 53, 62, 60, 47, 28, 17, 11,  8],
    'south':      [40, 55, 68, 65, 60, 52, 56, 64, 70, 60, 41, 28],
    'east':       [19, 28, 39, 45, 52, 54, 56, 50, 38, 26, 17, 13],
    'west':       [19, 28, 39, 45, 52, 54, 56, 50, 38, 26, 17, 13],
    'horizontal': [21, 36, 70, 105, 142, 154, 152, 128, 86, 49, 23, 15],
}

# =============================================================================
# KLIMASTANDORTE (mittlere monatliche Außentemperaturen, °C)
# Quelle: DWD TRY 2017, Mittelwerte 1995–2012 (vereinfacht)
# =============================================================================
CLIMATE_LOCATIONS = {
    'potsdam': {
        'label': 'Potsdam (DIN V 18599 Referenz)',
        'monthly_temps': [0.3, 1.0, 4.7, 9.0, 14.3, 17.0, 19.2, 18.9, 14.5, 9.7, 4.7, 1.5],
    },
    'berlin': {
        'label': 'Berlin',
        'monthly_temps': [0.6, 1.4, 5.0, 9.4, 14.7, 17.5, 19.6, 19.2, 14.7, 9.9, 4.9, 1.7],
    },
    'hamburg': {
        'label': 'Hamburg',
        'monthly_temps': [1.5, 1.9, 4.7, 8.5, 13.4, 16.3, 18.1, 18.0, 14.2, 10.0, 5.4, 2.5],
    },
    'muenchen': {
        'label': 'München',
        'monthly_temps': [-0.7, 0.6, 4.5, 8.4, 13.6, 16.6, 18.5, 18.0, 13.7, 9.0, 3.5, 0.0],
    },
    'freiburg': {
        'label': 'Freiburg (mild)',
        'monthly_temps': [2.4, 3.3, 6.9, 10.7, 15.3, 18.4, 20.3, 19.7, 15.7, 11.0, 6.0, 3.1],
    },
    'garmisch': {
        'label': 'Garmisch-Partenkirchen (alpin)',
        'monthly_temps': [-3.0, -1.8, 2.3, 6.4, 11.4, 14.5, 16.4, 15.9, 12.0, 7.4, 2.0, -2.0],
    },
}
DEFAULT_CLIMATE_LOCATION = 'potsdam'

DEFAULT_INDOOR_SETPOINT = 20.0
HEATING_LIMIT_TEMPERATURE = 15.0

# =============================================================================
# PRIMÄRENERGIEFAKTOREN nach GEG 2024 §22 / Anlage 4
# =============================================================================
PRIMARY_ENERGY_FACTORS = {
    'gas':         1.1,
    'oil':         1.1,
    'pellet':      0.2,
    'wood':        0.2,
    'district':    0.7,
    'district_re': 0.0,
    'heatpump':    1.8,
    'electricity': 1.8,
    'pv_self':     0.0,
}

NREN_PRIMARY_FACTORS = {
    'gas':         1.1,
    'oil':         1.1,
    'pellet':      0.2,
    'wood':        0.2,
    'district':    0.7,
    'district_re': 0.0,
    'heatpump':    1.2,
    'electricity': 1.2,
    'pv_self':     0.0,
}

# =============================================================================
# CO2-EMISSIONSFAKTOREN ENDENERGIE (kg CO2-äq / kWh Endenergie)
# Quelle: UBA 2024, Strommix DE 2024 ≈ 380 g/kWh
# =============================================================================
CO2_FACTORS = {
    'gas':         0.247,
    'oil':         0.318,
    'pellet':      0.036,
    'wood':        0.027,
    'district':    0.280,
    'district_re': 0.050,
    'heatpump':    0.380,
    'electricity': 0.380,
    'pv_self':     0.000,
}

# =============================================================================
# BEWERTUNGSGRENZEN
# =============================================================================
RATING_THRESHOLDS = {
    'excellent': 40,
    'medium':    80,
}
SYSTEM_RATING_THRESHOLDS = {
    'efficient': 60,
    'medium':   120,
}

# =============================================================================
# GEG-REFERENZGEBÄUDE (GEG 2024 Anlage 1, Wohngebäude)
# =============================================================================
GEG_REFERENCE_U_VALUES = {
    'wall_outside':   0.28,
    'roof':           0.20,
    'floor':          0.35,
    'window':         1.30,
    'door':           1.80,
    'g_value':        0.60,
    'thermal_bridge': 0.05,
    'air_change':     0.6,
}
GEG_REFERENCE_PRIMARY_LIMIT = 55  # kWh/(m²·a) vereinfachte Obergrenze Neubau

# =============================================================================
# WARMWASSER
# =============================================================================
DEFAULT_HOTWATER_DEMAND_PER_M2 = 12.5     # kWh/(m²·a) Wohngebäude (DIN V 18599-10)
DEFAULT_HOTWATER_DEMAND = 3000            # Legacy-Fallback

# =============================================================================
# HILFSENERGIE
# =============================================================================
DEFAULT_AUXILIARY_ELECTRICITY = 1200

# =============================================================================
# WÄRMEÜBERGÄNGE (DIN EN ISO 6946)
# =============================================================================
DEFAULT_R_SI = 0.13
DEFAULT_R_SE = 0.04

# =============================================================================
# LÜFTUNG
# =============================================================================
VENTILATION_CONSTANT = 0.34
DEFAULT_AIR_CHANGE_RATE = 0.5
DEFAULT_ROOM_HEIGHT = 3.0
DEFAULT_HEAT_RECOVERY = 0.0

# =============================================================================
# WÄRMEBRÜCKEN (DIN V 4108-6)
# =============================================================================
DEFAULT_THERMAL_BRIDGE_FACTOR = 0.10
THERMAL_BRIDGE_FACTOR_REDUCED = 0.05
THERMAL_BRIDGE_FACTOR_OPTIMIZED = 0.03

# =============================================================================
# INTERNE GEWINNE & NUTZUNG
# =============================================================================
DEFAULT_INTERNAL_GAINS_DENSITY = 3.0
DEFAULT_OCCUPANCY_HOURS = 8760
DEFAULT_GAIN_UTILIZATION_FACTOR = 0.75

# Wärmeabgabe pro Person (DIN EN ISO 13790 / DIN V 18599-10, sitzende Tätigkeit)
OCCUPANT_HEAT_OUTPUT_W = 70.0
# Standard-Personendichte (m² BGF / Person), Fallback Wohngebäude
DEFAULT_PERSONENDICHTE_M2_PER_PERSON = 40.0

# =============================================================================
# NUTZUNGSPROFILE nach DIN V 18599-10 (vereinfacht, je Gebäudetyp/-Variante)
# Werte: setpoint_temperature [°C], air_change_rate [1/h], occupancy_hours [h/a],
#        personendichte [m²/Person], equipment_gains [W/m²], lighting_gains [W/m²],
#        heat_recovery [-], gain_utilization_factor [-]
# =============================================================================
USAGE_PROFILES = {
    'wohngebaeude': {
        'label': 'Wohngebäude',
        'setpoint_temperature': 20.0,
        'air_change_rate':      0.5,
        'occupancy_hours':      8760,
        'personendichte':       40.0,
        'equipment_gains':      1.5,
        'lighting_gains':       0.5,
        'heat_recovery':        0.0,
        'gain_utilization_factor': 0.80,
    },
    'nicht_wohngebaeude': {
        'label': 'Nichtwohngebäude (Büro)',
        'setpoint_temperature': 20.0,
        'air_change_rate':      0.6,
        'occupancy_hours':      2500,
        'personendichte':       20.0,
        'equipment_gains':      4.0,
        'lighting_gains':       3.0,
        'heat_recovery':        0.5,
        'gain_utilization_factor': 0.75,
    },
}

# Feinere Defaults für Untervarianten (überschreiben USAGE_PROFILES[category])
USAGE_VARIANT_OVERRIDES = {
    'Einfamilienhaus':     {'personendichte': 40.0, 'air_change_rate': 0.5},
    'Mehrfamilienhaus':    {'personendichte': 35.0, 'air_change_rate': 0.5},
    'Reihenhaus':          {'personendichte': 38.0, 'air_change_rate': 0.5},
    'Doppelhaushälfte':    {'personendichte': 38.0, 'air_change_rate': 0.5},
    'Bürogebäude':         {'personendichte': 20.0, 'occupancy_hours': 2500, 'equipment_gains': 4.5, 'setpoint_temperature': 20.0},
    'Schulgebäude':        {'personendichte':  6.0, 'occupancy_hours': 1800, 'equipment_gains': 2.0, 'setpoint_temperature': 20.0},
    'Kindergarten':        {'personendichte':  6.0, 'occupancy_hours': 2000, 'equipment_gains': 2.0, 'setpoint_temperature': 21.0},
    'Verwaltungsgebäude':  {'personendichte': 20.0, 'occupancy_hours': 2500, 'equipment_gains': 4.5, 'setpoint_temperature': 20.0},
    'Hotel':               {'personendichte': 30.0, 'occupancy_hours': 4000, 'equipment_gains': 3.0, 'setpoint_temperature': 21.0},
    'Krankenhaus':         {'personendichte': 20.0, 'occupancy_hours': 8760, 'equipment_gains': 5.0, 'setpoint_temperature': 22.0},
    'Einzelhandel':        {'personendichte': 10.0, 'occupancy_hours': 3000, 'equipment_gains': 6.0, 'setpoint_temperature': 19.0},
    'Gewerbe/Werkstatt':   {'personendichte': 50.0, 'occupancy_hours': 2500, 'equipment_gains': 4.0, 'setpoint_temperature': 17.0},
    'Industriegebäude':    {'personendichte': 50.0, 'occupancy_hours': 4000, 'equipment_gains': 6.0, 'setpoint_temperature': 17.0},
}

# Höhenlagen-Korrektur Außentemperatur: ΔT ≈ -0.65 K pro 100 m über Stations-NN
ELEVATION_LAPSE_RATE_K_PER_M = 0.0065
REFERENCE_ELEVATION_M = 100.0  # ungefähre Referenzhöhe der CLIMATE_LOCATIONS-Datensätze

# =============================================================================
# BUNDESLAND → KLIMASTANDORT (nächster repräsentativer TRY-Standort)
# =============================================================================
STATE_TO_CLIMATE = {
    'Bayern':                 'muenchen',
    'Baden-Württemberg':      'freiburg',
    'Berlin':                 'berlin',
    'Brandenburg':            'potsdam',
    'Bremen':                 'hamburg',
    'Hamburg':                'hamburg',
    'Hessen':                 'potsdam',
    'Mecklenburg-Vorpommern': 'hamburg',
    'Niedersachsen':          'hamburg',
    'Nordrhein-Westfalen':    'potsdam',
    'Rheinland-Pfalz':        'freiburg',
    'Saarland':               'freiburg',
    'Sachsen':                'potsdam',
    'Sachsen-Anhalt':         'potsdam',
    'Schleswig-Holstein':     'hamburg',
    'Thüringen':              'potsdam',
}

# Spezifische Städte → Klima (überschreibt Bundesland-Mapping)
CITY_TO_CLIMATE = {
    'München':           'muenchen',
    'Garmisch-Partenkirchen': 'garmisch',
    'Berlin':            'berlin',
    'Hamburg':           'hamburg',
    'Freiburg':          'freiburg',
    'Potsdam':           'potsdam',
}

# =============================================================================
# FENSTER- / VERSCHATTUNGSFAKTOREN (DIN V 18599-2)
# =============================================================================
DEFAULT_G_VALUE = 0.60
FRAME_FACTOR_FF = 0.70
SHADING_FACTOR_FS_DEFAULT = 0.90
DIRT_FACTOR_FW = 0.90
NON_PERPENDICULAR_CORRECTION = 0.90

# =============================================================================
# ANLAGENTECHNIK
# =============================================================================
DEFAULT_EFFICIENCY = 0.92
DEFAULT_COP = 3.5
DEFAULT_COP_HOTWATER = 2.5

# =============================================================================
# PHOTOVOLTAIK
# =============================================================================
DEFAULT_PV_KWP = 8.0
DEFAULT_SPECIFIC_PV_YIELD = 950.0
DEFAULT_SELF_CONSUMPTION_RATE = 0.30
DEFAULT_ELECTRICITY_PRICE = 0.35
DEFAULT_FEED_IN_TARIFF = 0.08
PV_MONTHLY_DISTRIBUTION = [
    0.024, 0.045, 0.082, 0.110, 0.130, 0.130,
    0.135, 0.120, 0.090, 0.060, 0.045, 0.029,
]

# =============================================================================
# ENERGIEBILANZ
# =============================================================================
DEFAULT_HOUSEHOLD_ELECTRICITY = 2000
DEFAULT_ELECTRICITY_CO2_FACTOR = 0.38

# =============================================================================
# LEGACY (DEPRECATED) — vereinfachtes Gradstunden-Verfahren
# =============================================================================
# DIN V 4108-6 Anhang D, Wohngebäude, Standort Deutschland-Mittel,
# Innen 19 °C / Heizgrenze 12 °C → ca. 66 000 Kh/a.
# (Frühere Voreinstellung 78 000 lieferte unrealistisch hohe Heizwärmebedarfe.)
DEFAULT_GRADSTUNDEN = 66000

# =============================================================================
# VALIDIERUNG
# =============================================================================
VALID_HEATING_SYSTEMS = [
    "gas", "oil", "heatpump", "district", "district_re", "pellet", "wood",
]
MIN_EFFICIENCY = 0.0
MAX_EFFICIENCY = 1.2
MIN_COP = 0.0
MAX_COP = 10.0
MAX_U_VALUE = 6.0
MIN_G_VALUE = 0.0
MAX_G_VALUE = 1.0

# =============================================================================
# THERMISCHE GEBÄUDEMASSE C_m in Wh/(m²·K) — DIN EN ISO 13790
# =============================================================================
THERMAL_MASS_CLASSES = {
    'very_light': 22,
    'light':      45,
    'medium':     80,
    'heavy':     130,
    'very_heavy': 280,
}
DEFAULT_THERMAL_MASS_CLASS = 'medium'

HOURS_PER_MONTH = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
MONTH_LABELS = [
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
]
