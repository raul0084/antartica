"""Unit tests for the emissions calculation engine."""

import pytest
from core.emissions import EmissionsCalculator, EngineConfig, VoyageLeg


@pytest.fixture
def simple_voyage():
    engine = EngineConfig("Main Engine", power_kw=10000, sfc_g_per_kwh=180, fuel_type="HFO")
    return [VoyageLeg("At-Sea", duration_h=24, load_factor=0.75, engines=[engine])]


@pytest.fixture
def multi_leg_voyage():
    main = EngineConfig("Main Engine", power_kw=12000, sfc_g_per_kwh=175, fuel_type="HFO")
    aux  = EngineConfig("Auxiliary",   power_kw=1200,  sfc_g_per_kwh=210, fuel_type="MDO", num_units=2)
    return [
        VoyageLeg("Hotelling",   duration_h=8,  load_factor=0.0,  engines=[aux]),
        VoyageLeg("Manoeuvring", duration_h=1,  load_factor=0.25, engines=[main, aux]),
        VoyageLeg("At-Sea",      duration_h=48, load_factor=0.75, engines=[main, aux]),
    ]


# ---------------------------------------------------------------------------
# EngineConfig validation
# ---------------------------------------------------------------------------

def test_unsupported_fuel_raises():
    with pytest.raises(ValueError, match="Unsupported fuel type"):
        EngineConfig("Engine", power_kw=1000, sfc_g_per_kwh=180, fuel_type="COAL")


def test_negative_power_raises():
    with pytest.raises(ValueError):
        EngineConfig("Engine", power_kw=-100, sfc_g_per_kwh=180, fuel_type="HFO")


# ---------------------------------------------------------------------------
# VoyageLeg validation
# ---------------------------------------------------------------------------

def test_invalid_load_factor_raises():
    engine = EngineConfig("Engine", power_kw=1000, sfc_g_per_kwh=180, fuel_type="HFO")
    with pytest.raises(ValueError, match="Load factor"):
        VoyageLeg("Phase", duration_h=10, load_factor=1.5, engines=[engine])


def test_negative_duration_raises():
    engine = EngineConfig("Engine", power_kw=1000, sfc_g_per_kwh=180, fuel_type="HFO")
    with pytest.raises(ValueError, match="Duration"):
        VoyageLeg("Phase", duration_h=-5, load_factor=0.75, engines=[engine])


# ---------------------------------------------------------------------------
# Calculation correctness
# ---------------------------------------------------------------------------

def test_fuel_consumption_positive(simple_voyage):
    calc = EmissionsCalculator(simple_voyage)
    results = calc.calculate()
    assert results[0].fuel_consumption_kg > 0


def test_co2_emissions_positive(simple_voyage):
    calc = EmissionsCalculator(simple_voyage)
    results = calc.calculate()
    assert results[0].emissions_kg["CO2"] > 0


def test_zero_load_zero_fuel():
    aux = EngineConfig("Aux", power_kw=1000, sfc_g_per_kwh=200, fuel_type="MDO")
    legs = [VoyageLeg("Hotelling", duration_h=8, load_factor=0.0, engines=[aux])]
    calc = EmissionsCalculator(legs)
    results = calc.calculate()
    assert results[0].fuel_consumption_kg == 0.0


def test_summary_has_total_row(simple_voyage):
    calc = EmissionsCalculator(simple_voyage)
    calc.calculate()
    summary = calc.summary()
    assert "TOTAL" in summary["phase"].values


def test_total_co2e_is_sum_of_legs(multi_leg_voyage):
    calc = EmissionsCalculator(multi_leg_voyage)
    calc.calculate()
    total_from_method = calc.co2_equivalent_total()
    summary = calc.summary()
    total_from_summary = float(summary[summary["phase"] == "TOTAL"]["co2_equivalent_kg"].iloc[0])
    assert abs(total_from_method - total_from_summary) < 1e-6


def test_lng_has_zero_sox():
    engine = EngineConfig("LNG Engine", power_kw=5000, sfc_g_per_kwh=160, fuel_type="LNG")
    legs = [VoyageLeg("At-Sea", duration_h=24, load_factor=0.75, engines=[engine])]
    calc = EmissionsCalculator(legs)
    results = calc.calculate()
    assert results[0].emissions_kg["SOx"] == 0.0
