"""
Emission factors and constants for ship emissions calculations.

Sources:
- IMO MARPOL Annex VI
- Fourth IMO GHG Study 2020
- ICCT Ship Emissions Inventory

Units:
- Emission factors are in g/g_fuel (grams of pollutant per gram of fuel burned)
- LHV (Lower Heating Value) in MJ/kg
"""

# ---------------------------------------------------------------------------
# Fuel properties
# ---------------------------------------------------------------------------
FUEL_PROPERTIES = {
    "HFO": {           # Heavy Fuel Oil
        "lhv": 40.5,   # MJ/kg
        "density": 0.991,  # t/m³
        "carbon_content": 0.8600,
    },
    "MDO": {           # Marine Diesel Oil
        "lhv": 42.7,
        "density": 0.890,
        "carbon_content": 0.8744,
    },
    "LNG": {           # Liquefied Natural Gas
        "lhv": 48.0,
        "density": 0.470,
        "carbon_content": 0.7500,
    },
    "VLSFO": {         # Very Low Sulphur Fuel Oil (IMO 2020)
        "lhv": 40.5,
        "density": 0.991,
        "carbon_content": 0.8600,
    },
}

# ---------------------------------------------------------------------------
# Emission factors (g pollutant / g fuel)
# ---------------------------------------------------------------------------
EMISSION_FACTORS = {
    # CO2 factors derived from carbon content x 3.664 (MW ratio CO2/C)
    "CO2": {
        "HFO":   3.114,
        "MDO":   3.206,
        "LNG":   2.750,
        "VLSFO": 3.114,
    },
    # CH4 (methane) - more significant for LNG engines
    "CH4": {
        "HFO":   0.00006,
        "MDO":   0.00006,
        "LNG":   0.00600,
        "VLSFO": 0.00006,
    },
    # N2O
    "N2O": {
        "HFO":   0.00016,
        "MDO":   0.00016,
        "LNG":   0.00016,
        "VLSFO": 0.00016,
    },
    # NOx (as NO2 equivalent) - Tier II default
    "NOx": {
        "HFO":   0.0870,
        "MDO":   0.0870,
        "LNG":   0.0200,
        "VLSFO": 0.0870,
    },
    # SOx - strongly dependent on fuel sulphur content
    "SOx": {
        "HFO":   0.0540,   # ~2.7% S content (pre-IMO 2020)
        "MDO":   0.0020,   # <0.1% S
        "LNG":   0.0000,
        "VLSFO": 0.0020,   # <0.5% S (IMO 2020 cap)
    },
    # PM (particulate matter)
    "PM": {
        "HFO":   0.0014,
        "MDO":   0.0003,
        "LNG":   0.0001,
        "VLSFO": 0.0006,
    },
    # CO
    "CO": {
        "HFO":   0.0009,
        "MDO":   0.0009,
        "LNG":   0.0009,
        "VLSFO": 0.0009,
    },
}

# ---------------------------------------------------------------------------
# GWP (Global Warming Potential, 100-year horizon, AR5)
# ---------------------------------------------------------------------------
GWP_100 = {
    "CO2": 1,
    "CH4": 28,
    "N2O": 265,
}

# ---------------------------------------------------------------------------
# Engine load correction factors
# Multiplied against base emission factors to account for part-load operation
# Keys are fractional load (0.0-1.0), values are correction multipliers
# ---------------------------------------------------------------------------
LOAD_CORRECTION = {
    0.10: 1.30,
    0.25: 1.10,
    0.50: 1.00,
    0.75: 0.97,
    1.00: 1.00,
}

SUPPORTED_FUELS = list(FUEL_PROPERTIES.keys())
SUPPORTED_POLLUTANTS = list(EMISSION_FACTORS.keys())
