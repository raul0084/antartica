"""
Core emissions calculation engine.

Generalised from cruise ship models for Barcelona port (bachelor theses).
Supports any vessel type given appropriate input parameters.

Methodology:
    Emissions = Fuel Consumption x Emission Factor
    Fuel Consumption = Power x Load Factor x SFC x Time

Where:
    Power   - installed engine power (kW)
    SFC     - specific fuel consumption (g/kWh)
    Time    - operating hours in each phase

Phases modelled:
    - Hotelling   (at berth, auxiliary engines only)
    - Manoeuvring (low speed, main + auxiliary)
    - At-sea      (main engines at cruise load)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from .fuel_factors import (
    EMISSION_FACTORS,
    FUEL_PROPERTIES,
    GWP_100,
    LOAD_CORRECTION,
    SUPPORTED_FUELS,
    SUPPORTED_POLLUTANTS,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EngineConfig:
    """Represents a single engine or group of identical engines on the vessel."""
    name: str                    # e.g. "Main Engine", "Auxiliary"
    power_kw: float              # Installed power per unit (kW)
    sfc_g_per_kwh: float         # Specific fuel consumption (g/kWh)
    fuel_type: str = "HFO"       # Must be in SUPPORTED_FUELS
    num_units: int = 1           # Number of identical engines

    def __post_init__(self):
        if self.fuel_type not in SUPPORTED_FUELS:
            raise ValueError(
                f"Unsupported fuel type '{self.fuel_type}'. "
                f"Choose from: {SUPPORTED_FUELS}"
            )
        if self.power_kw <= 0:
            raise ValueError("Engine power must be positive.")
        if self.sfc_g_per_kwh <= 0:
            raise ValueError("SFC must be positive.")


@dataclass
class VoyageLeg:
    """A single operational phase (e.g. hotelling, manoeuvring, at-sea)."""
    phase: str               # Human-readable label
    duration_h: float        # Duration in hours
    load_factor: float       # Engine load as fraction of installed power (0-1)
    engines: list[EngineConfig] = field(default_factory=list)

    def __post_init__(self):
        if not (0.0 <= self.load_factor <= 1.0):
            raise ValueError("Load factor must be between 0 and 1.")
        if self.duration_h < 0:
            raise ValueError("Duration cannot be negative.")


@dataclass
class EmissionsResult:
    """Stores calculated emissions for a single voyage leg."""
    phase: str
    fuel_consumption_kg: float
    emissions_kg: dict[str, float]   # pollutant -> kg emitted
    co2_equivalent_kg: float         # CO2e using GWP100

    def to_series(self) -> pd.Series:
        data = {
            "phase": self.phase,
            "fuel_consumption_kg": self.fuel_consumption_kg,
            "co2_equivalent_kg": self.co2_equivalent_kg,
        }
        data.update({f"{p}_kg": v for p, v in self.emissions_kg.items()})
        return pd.Series(data)


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

class EmissionsCalculator:
    """
    Calculate ship emissions across multiple voyage legs.

    Example
    -------
    >>> main_engine = EngineConfig("Main Engine", power_kw=12000, sfc_g_per_kwh=175, fuel_type="HFO")
    >>> aux_engine  = EngineConfig("Auxiliary",   power_kw=1200,  sfc_g_per_kwh=210, fuel_type="MDO")
    >>>
    >>> legs = [
    ...     VoyageLeg("Hotelling",   duration_h=8,  load_factor=0.0,  engines=[aux_engine]),
    ...     VoyageLeg("Manoeuvring", duration_h=1,  load_factor=0.25, engines=[main_engine, aux_engine]),
    ...     VoyageLeg("At-Sea",      duration_h=48, load_factor=0.75, engines=[main_engine, aux_engine]),
    ... ]
    >>>
    >>> calc = EmissionsCalculator(legs)
    >>> results = calc.calculate()
    >>> summary = calc.summary()
    """

    def __init__(self, legs: list[VoyageLeg], pollutants: Optional[list[str]] = None):
        self.legs = legs
        self.pollutants = pollutants or SUPPORTED_POLLUTANTS
        self._results: list[EmissionsResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(self) -> list[EmissionsResult]:
        """Run the full calculation across all voyage legs."""
        self._results = [self._calculate_leg(leg) for leg in self.legs]
        return self._results

    def summary(self) -> pd.DataFrame:
        """Return a DataFrame with one row per phase plus a TOTAL row."""
        if not self._results:
            raise RuntimeError("Call calculate() before summary().")

        rows = [r.to_series() for r in self._results]
        df = pd.DataFrame(rows)

        # Add totals row (numeric columns only)
        numeric_cols = df.select_dtypes(include=np.number).columns
        total = df[numeric_cols].sum()
        total["phase"] = "TOTAL"
        df = pd.concat([df, total.to_frame().T], ignore_index=True)

        return df

    def co2_equivalent_total(self) -> float:
        """Return total CO2-equivalent emissions (kg) for the voyage."""
        if not self._results:
            raise RuntimeError("Call calculate() before co2_equivalent_total().")
        return sum(r.co2_equivalent_kg for r in self._results)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calculate_leg(self, leg: VoyageLeg) -> EmissionsResult:
        total_fuel_kg = 0.0
        total_emissions: dict[str, float] = {p: 0.0 for p in self.pollutants}

        for engine in leg.engines:
            fuel_kg = self._fuel_consumption(engine, leg.load_factor, leg.duration_h)
            total_fuel_kg += fuel_kg

            for pollutant in self.pollutants:
                ef = EMISSION_FACTORS[pollutant][engine.fuel_type]
                # ef is g/g_fuel -> same ratio as kg/kg_fuel -> multiply by fuel mass in kg
                total_emissions[pollutant] += ef * fuel_kg

        co2e = self._co2_equivalent(total_emissions)

        return EmissionsResult(
            phase=leg.phase,
            fuel_consumption_kg=total_fuel_kg,
            emissions_kg=total_emissions,
            co2_equivalent_kg=co2e,
        )

    @staticmethod
    def _fuel_consumption(engine: EngineConfig, load_factor: float, duration_h: float) -> float:
        """
        Calculate fuel consumption in kg.

        FC = P_installed x load_factor x load_correction x SFC x num_units x t / 1000
        """
        load_corr = EmissionsCalculator._interpolate_load_correction(load_factor)
        fc_g = (
            engine.power_kw
            * load_factor
            * load_corr
            * engine.sfc_g_per_kwh
            * engine.num_units
            * duration_h
        )
        return fc_g / 1000.0  # g -> kg

    @staticmethod
    def _interpolate_load_correction(load_factor: float) -> float:
        """Linearly interpolate load correction factor from the lookup table."""
        loads = sorted(LOAD_CORRECTION.keys())
        corrections = [LOAD_CORRECTION[k] for k in loads]
        return float(np.interp(load_factor, loads, corrections))

    @staticmethod
    def _co2_equivalent(emissions_kg: dict[str, float]) -> float:
        """Compute CO2-equivalent using GWP100."""
        return sum(
            emissions_kg.get(gas, 0.0) * gwp
            for gas, gwp in GWP_100.items()
        )
