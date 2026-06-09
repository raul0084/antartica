from .emissions import calculate_emissions, calculate_uncertainty
from .data_handling import (
    enrich_calls_with_vessel_data, 
    attach_emission_factors, 
    classify_by_eslora, 
    group_emissions, 
    calculate_operational_times,
    apply_labels
)
import pandas as pd

def run_pipeline(df_calls, df_vessels, EF, U):

    df_calls["year"] = pd.to_datetime(df_calls["etautc"]).dt.year
    df_calls["date"] = pd.to_datetime(df_calls["etautc"])
    # Enrich with vessel data
    df, df_unmatched = enrich_calls_with_vessel_data(df_calls, df_vessels)

    # Compute times
    df = calculate_operational_times(df)

    # Emission factors
    df = attach_emission_factors(df, EF)

    # Emissions
    df = calculate_emissions(df)

    # Uncertainty
    df = calculate_uncertainty(df, U)

    # Add classification by eslora
    df = classify_by_eslora(df)



    # KPIs
    kpis = {
        "Total": group_emissions(df),
        "Per_Fuel": group_emissions(df, ["fuel"]),
        "Per_Eslora": group_emissions(df, ["eslora_rang"]),
        "Per_Terminal": group_emissions(df, ["terminalnom"]),
        "Per_Consignatari": group_emissions(df, ["consignatari"]),
        "Totals_byYear": group_emissions(df, ["year"]),
        "Per_Fuel_byYear": group_emissions(df, ["year", "fuel"]),
        "Per_Eslora_byYear": group_emissions(df, ["year", "eslora_rang"]),
    }

    df = apply_labels(df)

    return df, kpis, df_unmatched