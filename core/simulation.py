"""
simulation.py

Runs a single, manually-specified voyage through the same emissions +
uncertainty engine used by the batch pipeline (emissions.py /
data_handling.py), instead of a full port_calls/vessels dataset.

Intended use: a "what-if" / single-voyage page (e.g. an Antarctic
expedition leg) where the user supplies vessel specs and operational
times directly, rather than pulling them from the calls/vessels tables.
"""

from datetime import date

import pandas as pd

from .data_handling import attach_emission_factors, classify_by_eslora, apply_labels
from .emissions import calculate_emissions, calculate_uncertainty

# Same defaults used in data_handling.enrich_calls_with_vessel_data,
# kept here so a simulated voyage matches batch-pipeline assumptions
# unless the user overrides them.
DEFAULT_LOAD_FACTORS = {
    "lf_main": 0.2,
    "lf_aux_nav": 0.2,
    "lf_aux_mani": 0.5,
    "lf_aux_hot": 0.4,
}

REQUIRED_FIELDS = [
    "p_main", "p_aux", "p_gt", "fuel", "eslora_metres",
    "nav_time", "mani_time", "hot_time",
]


def build_voyage_row(inputs: dict) -> pd.DataFrame:
    """
    Turns a dict of manual voyage inputs into a 1-row DataFrame with the
    schema attach_emission_factors() / calculate_emissions() expect.

    Required keys in `inputs`:
        p_main, p_aux, p_gt   -- engine/gross tonnage power (kW / GT)
        fuel                  -- must match a key in your EF table (case-insensitive)
        eslora_metres         -- vessel length (m)
        nav_time, mani_time, hot_time -- hours in each mode

    Optional keys (fall back to pipeline defaults if omitted):
        lf_main, lf_aux_nav, lf_aux_mani, lf_aux_hot
        voyage_date -- date/datetime/str; defaults to today if omitted.
            Populates 'year' and 'date' the same way run_pipeline() does
            for real port calls, so downstream code (labels, report
            filenames, year-based grouping) works identically for a
            simulated voyage.
    """
    missing = [f for f in REQUIRED_FIELDS if inputs.get(f) is None]
    if missing:
        raise ValueError(f"Missing required simulation inputs: {', '.join(missing)}")

    row = {**DEFAULT_LOAD_FACTORS, **inputs}
    row["fuel"] = str(row["fuel"]).lower().strip()

    voyage_date = pd.to_datetime(row.pop("voyage_date", None) or date.today())
    row["year"] = voyage_date.year
    row["date"] = voyage_date

    return pd.DataFrame([row])


def run_single_voyage(inputs: dict, EF: dict, U: dict) -> pd.DataFrame:  # Parallel to run_pipeline()
    """
    Runs one manually-specified voyage through calculate_emissions /
    calculate_uncertainty and returns a 1-row, human-labelled DataFrame
    (same column labels as the batch pipeline output).

    Raises ValueError if the fuel isn't found in the EF table, so a typo
    doesn't silently produce a row of NaNs.
    """
    df = build_voyage_row(inputs)
    df = attach_emission_factors(df, EF)

    ef_cols = [c for c in df.columns if c.startswith("ef_main_")]
    if not ef_cols or df[ef_cols].isna().all(axis=None):
        raise ValueError(
            f"Fuel '{inputs['fuel']}' not found in emission factors table. "
            f"Available fuels: {sorted(k for k in EF.keys() if isinstance(EF[k], dict))}"
        )

    df = calculate_emissions(df)
    df = calculate_uncertainty(df, U)
    df = classify_by_eslora(df)
    df = apply_labels(df)

    return df


def summarize_voyage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Long-format summary of a run_single_voyage() result: one row per
    pollutant with total emissions and its uncertainty, both in tonnes.
    Convenient for a results table or bar chart in the UI.
    """
    total_cols = [c for c in df.columns if c.endswith("total (t)")]

    rows = []
    for col in total_cols:
        pollutant = col.replace(" total (t)", "")
        sigma_col = f"σ {pollutant} (t)"
        rows.append({
            "Pollutant": pollutant,
            "Emissions (t)": df[col].iloc[0],
            "Uncertainty (t)": df[sigma_col].iloc[0] if sigma_col in df.columns else None,
        })

    return pd.DataFrame(rows)