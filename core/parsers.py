"""
Parsers for user-supplied CSV/Excel voyage data.

Expected columns (case-insensitive, spaces replaced with underscores):
    phase           - name of the voyage leg (str)
    duration_h      - duration in hours (float)
    load_factor     - engine load 0-1 (float)
    engine_name     - label for the engine (str)
    power_kw        - installed engine power per unit (float)
    sfc_g_per_kwh   - specific fuel consumption (float)
    fuel_type       - one of HFO, MDO, LNG, VLSFO (str)
    num_units       - number of identical engines (int, optional, default 1)

Each row represents one engine in one voyage phase.
Multiple engines in the same phase share the same phase/duration/load_factor values.
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

from .emissions import EngineConfig, VoyageLeg
from .fuel_factors import SUPPORTED_FUELS


REQUIRED_COLUMNS = {
    "phase", "duration_h", "load_factor",
    "engine_name", "power_kw", "sfc_g_per_kwh", "fuel_type",
}


def parse_voyage_file(filepath: str | Path) -> list[VoyageLeg]:
    """
    Read a CSV or Excel file and return a list of VoyageLeg objects.

    Parameters
    ----------
    filepath : str or Path
        Path to .csv or .xlsx file.

    Returns
    -------
    list[VoyageLeg]
    """
    filepath = Path(filepath)

    if filepath.suffix == ".csv":
        df = pd.read_csv(filepath)
    elif filepath.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file type: {filepath.suffix}")

    # Normalise column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    _validate_columns(df)
    df = _coerce_types(df)

    return _build_legs(df)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_columns(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    bad_fuels = set(df["fuel_type"].str.upper().unique()) - set(SUPPORTED_FUELS)
    if bad_fuels:
        raise ValueError(
            f"Unsupported fuel types in file: {bad_fuels}. "
            f"Supported: {SUPPORTED_FUELS}"
        )


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["duration_h"]    = pd.to_numeric(df["duration_h"],    errors="raise")
    df["load_factor"]   = pd.to_numeric(df["load_factor"],   errors="raise")
    df["power_kw"]      = pd.to_numeric(df["power_kw"],      errors="raise")
    df["sfc_g_per_kwh"] = pd.to_numeric(df["sfc_g_per_kwh"], errors="raise")
    df["num_units"]     = pd.to_numeric(
        df["num_units"] if "num_units" in df.columns else 1,
        errors="raise"
    ).fillna(1).astype(int)
    df["fuel_type"] = df["fuel_type"].str.strip().str.upper()
    return df


def _build_legs(df: pd.DataFrame) -> list[VoyageLeg]:
    legs = []
    for (phase, duration_h, load_factor), group in df.groupby(
        ["phase", "duration_h", "load_factor"], sort=False
    ):
        engines = [
            EngineConfig(
                name=row["engine_name"],
                power_kw=row["power_kw"],
                sfc_g_per_kwh=row["sfc_g_per_kwh"],
                fuel_type=row["fuel_type"],
                num_units=int(row["num_units"]),
            )
            for _, row in group.iterrows()
        ]
        legs.append(VoyageLeg(
            phase=phase,
            duration_h=float(duration_h),
            load_factor=float(load_factor),
            engines=engines,
        ))
    return legs
