import pandas as pd
import numpy as np

# USED TO SLIM DATA INTO ONLY VESSELS IN CALLS
def load_vessels_for_calls(df_calls, df_vessels):
    """
    Filters and prepares vessel data to match df_calls.

    Parameters:
        df_calls (DataFrame): port calls
        df_vessels_raw (DataFrame): full vessel table from DB

    Returns:
        df_vessels (DataFrame): cleaned + filtered
    """

    # -------------------------
    # NORMALIZE KEYS
    # -------------------------
    df_calls = df_calls.copy()
    df_vessels = df_vessels.copy()

    # IMO as string
    df_calls["imo"] = df_calls["imo"].astype(str).str.strip()
    df_vessels["imo"] = df_vessels["imo"].astype(str).str.strip()

    # Vessel name normalized
    df_calls["vaixellnom_clean"] = df_calls["vaixellnom"].str.lower().str.strip()
    df_vessels["vaixellnom_clean"] = df_vessels["vaixellnom"].str.lower().str.strip()

    # Fuel normalized
    df_vessels["fuel"] = df_vessels["fuel"].str.lower().str.strip()

    # -------------------------
    # FILTER ONLY MATCHING VESSELS
    # -------------------------
    imo_set = set(df_calls["imo"].dropna())
    mmsi_set = set(df_calls["mmsi"].dropna())
    name_set = set(df_calls["vaixellnom_clean"].dropna())

    df_vessels = df_vessels[
        (df_vessels["imo"].isin(imo_set)) |
        (df_vessels["mmsi"].isin(mmsi_set)) |
        (df_vessels["vaixellnom_clean"].isin(name_set))
    ]

    # -------------------------
    # REMOVE DUPLICATES (IMPORTANT)
    # -------------------------
    df_vessels = df_vessels.drop_duplicates(subset=["imo", "mmsi", "vaixellnom_clean"])

    # -------------------------
    # KEEP ONLY NEEDED COLUMNS
    # -------------------------
    df_vessels = df_vessels[
        [
            "imo",
            "mmsi",
            "vaixellnom",
            "vaixellnom_clean",
            "p_main",
            "p_aux",
            "p_gt",
            "fuel"
        ]
    ]

    return df_vessels

# ADDS "p_main, p_aux, p_gt, lf_main, lf_aux_nav, lf_aux_mani, lf_aux_hot" TO CALLS DF
def enrich_calls_with_vessel_data(
    df_calls,
    df_vessels
):
    """
    Adds P_main, P_aux, fuel and default load factors to df_calls.
    Matches vessels using imo, mmsi or vessel_name.
    """

    # -------------------------
    # DEFAULTS
    # -------------------------
    DEFAULT_P_MAIN = 10000
    DEFAULT_P_AUX  = 2000
    DEFAULT_P_GT   = 5000
    DEFAULT_FUEL   = "mdo/mgo"

    LF_main = 0.8
    LF_aux_nav = 0.3
    LF_aux_mani = 0.5
    LF_aux_hot = 0.2

    # -------------------------
    # CLEAN KEYS
    # -------------------------
    df_vessels = df_vessels.copy()
    df_calls = df_calls.copy()

    df_vessels["vaixellnom_clean"] = df_vessels["vaixellnom"].str.lower().str.strip()
    df_calls["vaixellnom_clean"] = df_calls["vaixellnom"].str.lower().str.strip()

    # Ensure consistent types
    df_calls["imo"] = df_calls["imo"].astype("string").str.strip()
    df_vessels["imo"] = df_vessels["imo"].astype("string").str.strip()

    df_calls["mmsi"] = df_calls["mmsi"].astype("string").str.strip()
    df_vessels["mmsi"] = df_vessels["mmsi"].astype("string").str.strip()

    # Normalize fuel
    df_vessels["fuel"] = df_vessels["fuel"].str.lower().str.strip()

    # -------------------------
    # MERGE BY IMO FIRST
    # -------------------------
    df = df_calls.merge(
        df_vessels[["imo", "p_main", "p_aux", "p_gt", "fuel"]],
        on="imo",
        how="left"
    )

    # -------------------------
    # FILL MISSING VIA MMSI
    # -------------------------
    mask = df["p_main"].isna()

    df_mmsi = df_calls[mask].merge(
        df_vessels[["mmsi", "p_main", "p_aux", "p_gt", "fuel"]],
        on="mmsi",
        how="left"
    )

    df.loc[mask, ["p_main", "p_aux", "p_gt", "fuel"]] = df_mmsi[
        ["p_main", "p_aux", "p_gt", "fuel"]
    ].values

    # -------------------------
    # FILL MISSING VIA NAME
    # -------------------------
    mask = df["p_main"].isna()

    df_name = df_calls[mask].merge(
        df_vessels[["vaixellnom_clean", "p_main", "p_aux", "p_gt", "fuel"]],
        on="vaixellnom_clean",
        how="left"
    )

    df.loc[mask, ["p_main", "p_aux", "p_gt", "fuel"]] = df_name[
        ["p_main", "p_aux", "p_gt", "fuel"]
    ].values

    # -------------------------
    # DEFAULT FALLBACK
    # -------------------------
    df["p_main"] = df["p_main"].fillna(DEFAULT_P_MAIN)
    df["p_aux"] = df["p_aux"].fillna(DEFAULT_P_AUX)
    df["p_gt"] = df["p_gt"].fillna(DEFAULT_P_GT)
    df["fuel"] = df["fuel"].fillna(DEFAULT_FUEL)

    # -------------------------
    # LOAD FACTORS
    # -------------------------
    df["lf_main"] = LF_main
    df["lf_aux_nav"] = LF_aux_nav
    df["lf_aux_mani"] = LF_aux_mani
    df["lf_aux_hot"] = LF_aux_hot

    return df

# CALCULATE TIMES FOR NAV, MAN, AND HOT
def calculate_operational_times(df):

    df = df.copy()

    # --- hot time (from data)
    df["hot_time"] = (
        pd.to_datetime(df["etdutc"], errors="coerce") -
        pd.to_datetime(df["etautc"], errors="coerce")
    ).dt.total_seconds() / 3600

    df["hot_time"] = df["hot_time"].clip(lower=0)
    df["hot_time"] = df["hot_time"].fillna(24)

    # --- defaults
    df["mani_time"] = 1.0
    df["nav_time"] = 0.5

    return df



# GET EMISSION FACTORS AS A DF
def build_ef_table(EF_DATA):
    """
    Converts EF_DATA JSON into a wide DataFrame ready to merge.
    """

    rows = []

    for fuel, data in EF_DATA.items():

        # -------------------------
        # SKIP NON-FUEL KEYS
        # -------------------------
        if not isinstance(data, dict):
            continue

        if "main" not in data or "aux" not in data:
            continue

        fuel_clean = fuel.lower().strip()

        row = {"fuel": fuel_clean}

        for pollutant in data["main"].keys():
            p = pollutant.lower()

            row[f"ef_main_{p}"] = data["main"][pollutant]
            row[f"ef_aux_{p}"]  = data["aux"][pollutant]

        rows.append(row)

    return pd.DataFrame(rows)

# ATTARCH EMISSION FACTORS TO CALLS
def attach_emission_factors(df_calls, EF_DATA):

    df = df_calls.copy()

    # normalize fuel
    df["fuel"] = df["fuel"].str.lower().str.strip()

    # build EF table
    df_ef = build_ef_table(EF_DATA)

    # merge
    df = df.merge(df_ef, on="fuel", how="left")

    return df

# GROUP BY COLS AND POLLUTANTS (ALSO GROUPS UNCERTAINTY USING SQRT(SUM(SIGMA^2)))
def group_emissions(
    df,
    group_cols=None,
    pollutant_cols=None,
    sigma_cols=None
):
    """
    Aggregates emissions (tonnes) and uncertainty (tonnes).
    """

    if pollutant_cols is None:
        pollutant_cols = [c for c in df.columns if c.endswith(" (t)") and not c.startswith("σ")]

    if sigma_cols is None:
        sigma_cols = [c for c in df.columns if c.startswith("σ")]

    # -------------------------
    # NO GROUPING (TOTAL)
    # -------------------------
    if group_cols is None:

        emissions = df[pollutant_cols].sum()

        sigma = np.sqrt((df[sigma_cols]**2).sum())

        result = pd.concat([emissions, sigma]).to_frame().T
        result.index = ["total"]

    # -------------------------
    # GROUPED
    # -------------------------
    else:

        # emissions → sum
        emissions = (
            df.groupby(group_cols)[pollutant_cols]
            .sum()
        )

        # uncertainty → sqrt(sum of squares)
        sigma = (
            df.groupby(group_cols)[sigma_cols]
            .apply(lambda x: np.sqrt((x**2).sum()))
        )

        result = emissions.join(sigma).reset_index()

    return result

# CLASSIFY BY ESLORA
def classify_by_eslora(df, col="eslora_metres"):
    """
    Classifies ships into length categories based on 'eslora' (meters).
    """

    df = df.copy()

    # Ensure numeric
    eslora_numeric = pd.to_numeric(df[col], errors='coerce')

    # Define bins
    bins = [-np.inf, 100, 200, 300, np.inf]
    labels = ["<100m", "100-200m", "200-300m", ">300m"]

    # Categorize
    df["eslora_rang"] = pd.cut(
        eslora_numeric,
        bins=bins,
        labels=labels,
        right=False
    )

    return df

# QUALITY CONTROL
def build_qc_summary(df):

    summary = {}

    # Coverage
    summary["total_calls"] = len(df)
    summary["matched_calls"] = df["p_main"].notna().sum()
    summary["coverage_pct"] = 100 * summary["matched_calls"] / max(summary["total_calls"], 1)

    # Time issues
    summary["negative_hot_time"] = (df["hot_time"] < 0).sum()
    summary["hot_time_gt_72h"] = (df["hot_time"] > 72).sum()

    # Emission consistency (example with CO)
    if "E_total_co_g" in df.columns:
        diff = df["E_total_co_g"] - (
            df["E_nav_co_g"] +
            df["E_mani_co_g"] +
            df["E_hot_co_g"]
        )
        summary["consistency_errors"] = (diff.abs() > 1e-6).sum()

    return pd.DataFrame([summary])

# CHANGES LABLES TO READABLE NAMES
COLUMN_LABELS = {
    # --- Identifiers & vessel info ---
    "vaixellnom_clean":     "Vessel name",
    "vaixellnom":           "Vessel name (raw)",
    "vaixelltipus":         "Vessel type",
    "vaixellbanderanom":    "Flag",
    "vaixellbanderacodi":   "Flag code",
    "mmsi":                 "MMSI",
    "imo":                  "IMO",
    "callsign":             "Call sign",
    "consignatari":         "Consignee",

    # --- Port & terminal ---
    "terminalnom":          "Terminal",
    "terminalcodi":         "Terminal code",
    "mollcodi":             "Berth code",
    "mollmoduls":           "Berth modules",
    "portorigennom":        "Port of origin",
    "portorigencodi":       "Port of origin code",
    "portdestinom":         "Port of destination",
    "portdesticodi":        "Port of destination code",

    # --- Call info ---
    "escalanum":            "Call number",
    "escalaestat":          "Call status",
    "estoperatiuid":        "Operational state",
    "anyescala":            "Call year",
    "mesinfo":              "More Info",
    "year":                 "Year",
    "date":                 "Date",

    # --- Times ---
    # "eta":                  "ETA",
    # "etautc":               "ETA (UTC)",
    # "etadia":               "ETA day",
    # "etahora":              "ETA hour",
    # "etd":                  "ETD",
    # "etdutc":               "ETD (UTC)",
    # "etddia":               "ETD day",
    # "etdhora":              "ETD hour",

    # --- Vessel dimensions ---
    "eslora_metres":        "LOA (m)",
    "eslora_rang":          "LOA range",
    "manega_metres":        "Beam (m)",
    "calat_metres":         "Draft (m)",

    # --- Engine & fuel ---
    "p_main":               "Main engine power (kW)",
    "p_aux":                "Aux engine power (kW)",
    "p_gt":                 "GT",
    "fuel":                 "Fuel type",
    "lf_main":              "Load factor (main)",
    "lf_aux_nav":           "Load factor aux (nav)",
    "lf_aux_mani":          "Load factor aux (mani)",
    "lf_aux_hot":           "Load factor aux (hotelling)",

    # --- Time at mode ---
    "nav_time":             "Nav time (h)",
    "mani_time":            "Manoeuvring time (h)",
    "hot_time":             "Hotelling time (h)",

    # --- Emission factors ---
    "ef_main_co":           "EF main CO",
    "ef_aux_co":            "EF aux CO",
    "ef_main_nox":          "EF main NOx",
    "ef_aux_nox":           "EF aux NOx",
    "ef_main_nmvoc":        "EF main NMVOC",
    "ef_aux_nmvoc":         "EF aux NMVOC",
    "ef_main_tsp_pm":       "EF main TSP/PM",
    "ef_aux_tsp_pm":        "EF aux TSP/PM",
    "ef_main_bc":           "EF main BC",
    "ef_aux_bc":            "EF aux BC",
    "ef_main_sfoc":         "EF main SFOC",
    "ef_aux_sfoc":          "EF aux SFOC",
    "cf":                   "Carbon factor",

    # --- Emissions by mode (tonnes) ---
    "E_nav_co_g":           "CO nav (t)",
    "E_mani_co_g":          "CO mani (t)",
    "E_hot_co_g":           "CO hotelling (t)",
    "E_total_co_g":         "CO total (t)",

    "E_nav_nox_g":          "NOx nav (t)",
    "E_mani_nox_g":         "NOx mani (t)",
    "E_hot_nox_g":          "NOx hotelling (t)",
    "E_total_nox_g":        "NOx total (t)",

    "E_nav_nmvoc_g":        "NMVOC nav (t)",
    "E_mani_nmvoc_g":       "NMVOC mani (t)",
    "E_hot_nmvoc_g":        "NMVOC hotelling (t)",
    "E_total_nmvoc_g":      "NMVOC total (t)",

    "E_nav_tsp_pm_g":       "TSP/PM nav (t)",
    "E_mani_tsp_pm_g":      "TSP/PM mani (t)",
    "E_hot_tsp_pm_g":       "TSP/PM hotelling (t)",
    "E_total_tsp_pm_g":     "TSP/PM total (t)",

    "E_nav_bc_g":           "BC nav (t)",
    "E_mani_bc_g":          "BC mani (t)",
    "E_hot_bc_g":           "BC hotelling (t)",
    "E_total_bc_g":         "BC total (t)",

    "E_nav_sfoc_g":         "SFOC nav (t)",
    "E_mani_sfoc_g":        "SFOC mani (t)",
    "E_hot_sfoc_g":         "SFOC hotelling (t)",
    "E_total_sfoc_g":       "SFOC total (t)",

    "E_total_co2_g":        "CO2 total (t)",

    # --- Uncertainties (tonnes) ---
    "sigma_co_g":           "σ CO (t)",
    "sigma_nox_g":          "σ NOx (t)",
    "sigma_nmvoc_g":        "σ NMVOC (t)",
    "sigma_tsp_pm_g":       "σ TSP/PM (t)",
    "sigma_bc_g":           "σ BC (t)",
    "sigma_sfoc_g":         "σ SFOC (t)",
    "sigma_co2_g":          "σ CO2 (t)",
}
def apply_labels(df):
    """
    Renames columns to readable labels and optionally converts
    emission and uncertainty columns from grams to tonnes.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame with renamed columns and converted units.
    """

    df = df.rename(columns=COLUMN_LABELS)

    return df

# Probably won't use
def build_detall_cols(df, emit_cols=None, include_sigma=False):
    """
    - Select base + emission columns (only those that exist)
    - Auto-detect emission columns if not provided
    - Sort by etautc and VAIXELLNOM if present
    """

    # -------------------------
    # BASE COLUMNS
    # -------------------------
    base_cols = [
        'year', 'vaixellnom', 'imo', 'mmsi',
        'fuel', 'horesport',
        'nav_time', 'mani_time', 'hot_time',
        'terminalnom', 'consignatari',
        'eslora_metres', 'eslora_rang',
        'p_main', 'p_aux',
        'etautc', 'etdutc'
    ]

    # -------------------------
    # AUTO DETECT EMISSIONS
    # -------------------------
    if emit_cols is None:
        emit_cols = [c for c in df.columns if c.startswith("E_")]

    # Optionally include uncertainty
    if include_sigma:
        sigma_cols = [c for c in df.columns if c.startswith("sigma_")]
        emit_cols = emit_cols + sigma_cols

    # -------------------------
    # COMBINE
    # -------------------------
    wanted_cols = base_cols + emit_cols

    # Keep only existing columns
    wanted_cols = [col for col in wanted_cols if col in df.columns]

    # -------------------------
    # SELECT
    # -------------------------
    resultats = df[wanted_cols].copy()

    # -------------------------
    # SORT
    # -------------------------
    if 'etautc' in resultats.columns and 'vaixellnom' in resultats.columns:
        resultats = resultats.sort_values(by=['etautc', 'vaixellnom'])

    return resultats




