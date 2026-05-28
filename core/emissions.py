import pandas as pd
import numpy as np

# CALCULATES EMISSIONS PER POLLUTANT PER ROW IN DF
def calculate_emissions(df):
    """
    Calculates emissions for all pollutants in a fully vectorized way.

    Requires:
        - p_main, p_aux
        - lf_main, lf_aux_nav, lf_aux_mani, lf_aux_hot
        - nav_time, mani_time, hot_time
        - ef_main_*, ef_aux_*

    Returns:
        df with emission columns added
    """

    df = df.copy()

    # -------------------------
    # DETECT POLLUTANTS
    # -------------------------
    ef_main_cols = [c for c in df.columns if c.startswith("ef_main_")]
    pollutants = [c.replace("ef_main_", "") for c in ef_main_cols]

    # -------------------------
    # LOOP (lightweight, column-wise)
    # -------------------------
    for p in pollutants:

        ef_main = df[f"ef_main_{p}"].div(1e6)
        ef_aux  = df[f"ef_aux_{p}"].div(1e6)

        # -------------------------
        # MAIN ENGINE
        # -------------------------
        E_main_nav  = df["p_main"] * df["lf_main"] * ef_main * df["nav_time"]
        E_main_mani = df["p_main"] * df["lf_main"] * ef_main * df["mani_time"]
        E_main_hot  = 0  # always zero

        # -------------------------
        # AUX ENGINE
        # -------------------------
        E_aux_nav  = df["p_aux"] * df["lf_aux_nav"]  * ef_aux * df["nav_time"]
        E_aux_mani = df["p_aux"] * df["lf_aux_mani"] * ef_aux * df["mani_time"]
        E_aux_hot  = df["p_aux"] * df["lf_aux_hot"]  * ef_aux * df["hot_time"]

        # -------------------------
        # TOTALS
        # -------------------------
        df[f"E_nav_{p}_g"]  = E_main_nav  + E_aux_nav
        df[f"E_mani_{p}_g"] = E_main_mani + E_aux_mani
        df[f"E_hot_{p}_g"]  = E_main_hot  + E_aux_hot
        df[f"E_total_{p}_g"] = (
            df[f"E_nav_{p}_g"] +
            df[f"E_mani_{p}_g"] +
            df[f"E_hot_{p}_g"]
        )

    return df

# CALCULATES UNCERTANTIES PER ROW
def calculate_uncertainty(df, U):
    """
    Computes uncertainty (sigma) for each pollutant in a vectorized way.

    Parameters:
        df: DataFrame with emissions + EF + power + time
        U: uncertainties dict

    Returns:
        df with sigma columns added
    """

    df = df.copy()

    # -------------------------
    # DETECT POLLUTANTS
    # -------------------------
    ef_main_cols = [c for c in df.columns if c.startswith("ef_main_")]
    pollutants = [c.replace("ef_main_", "") for c in ef_main_cols]

    for p in pollutants:

        ef_main = df[f"ef_main_{p}"]
        ef_aux  = df[f"ef_aux_{p}"]

        uEF = U["ef"][p]

        # -------------------------
        # REBUILD COMPONENTS
        # -------------------------
        E_main_nav  = df["p_main"] * df["lf_main"] * ef_main * df["nav_time"]
        E_main_mani = df["p_main"] * df["lf_main"] * ef_main * df["mani_time"]

        E_aux_nav  = df["p_aux"] * df["lf_aux_nav"]  * ef_aux * df["nav_time"]
        E_aux_mani = df["p_aux"] * df["lf_aux_mani"] * ef_aux * df["mani_time"]
        E_aux_hot  = df["p_aux"] * df["lf_aux_hot"]  * ef_aux * df["hot_time"]

        # -------------------------
        # RULE B (product)
        # -------------------------
        sig_main_nav = np.abs(E_main_nav) * np.sqrt(
            U["p_main"]**2 + U["lf_main"]**2 + uEF**2 + U["t_nav"]**2
        )

        sig_main_mani = np.abs(E_main_mani) * np.sqrt(
            U["p_main"]**2 + U["lf_main"]**2 + uEF**2 + U["t_mani"]**2
        )

        sig_aux_nav = np.abs(E_aux_nav) * np.sqrt(
            U["p_aux"]**2 + U["lf_aux_nav"]**2 + uEF**2 + U["t_nav"]**2
        )

        sig_aux_mani = np.abs(E_aux_mani) * np.sqrt(
            U["p_aux"]**2 + U["lf_aux_mani"]**2 + uEF**2 + U["t_mani"]**2
        )

        sig_aux_hot = np.abs(E_aux_hot) * np.sqrt(
            U["p_aux"]**2 + U["lf_aux_hot"]**2 + uEF**2 + U["t_hot"]**2
        )

        # -------------------------
        # RULE A (sum)
        # -------------------------
        sigma_total = np.sqrt(
            sig_main_nav**2 +
            sig_main_mani**2 +
            sig_aux_nav**2 +
            sig_aux_mani**2 +
            sig_aux_hot**2
        )

        df[f"sigma_{p}_g"] = sigma_total

    # =========================
    # CO2 from SFOC
    # =========================
    if "ef_main_sfoc" in df.columns:

        CF_MDO = 3.206
        CF_LNG = 2.750

        # map CF by fuel
        df["cf"] = np.where(
            df["fuel"] == "lng",
            CF_LNG,
            CF_MDO
        )

        # CO2 emissions
        df["E_total_co2_g"] = df["E_total_sfoc_g"] * df["cf"]

        # uncertainty
        uSFOC = U["ef"]["sfoc"]
        uCF   = U["cf"]

        df["sigma_co2_g"] = np.abs(df["E_total_co2_g"]) * np.sqrt(
            uSFOC**2 + uCF**2
        )

    return df












