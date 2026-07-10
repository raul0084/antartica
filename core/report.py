import io  
import pandas as pd
from datetime import datetime
from pathlib import Path
from .data_handling import group_emissions

def get_default_path(df_calls=None, base_dir=None):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if df_calls is not None and "Year" in df_calls.columns:
        ymin = df_calls["Year"].min()
        ymax = df_calls["Year"].max()
        filename = f"emissions_{ymin}_{ymax}_{ts}.xlsx"
    else:
        filename = f"emissions_{ts}.xlsx"
    return filename

def generate_excel_report(df_calls, kpis=None, qc_summary=None):
    """
    Generates Excel report in memory and returns the filename and raw data bytes.
    """
    if kpis is None:
        total = group_emissions(df_calls)
        by_fuel = group_emissions(df_calls, ["Fuel type"])
        by_terminal = group_emissions(df_calls, ["Terminal"])
        by_consignatari = group_emissions(df_calls, ["Consignee"])

        kpis = {
            "All_Calls": df_calls,
            "Total": total,
            "Per_Fuel": by_fuel,
            "Per_Terminal": by_terminal,
            "Per_Consignatari": by_consignatari
        }

    filename = get_default_path(df_calls)

    # -------------------------
    # WRITE EXCEL TO MEMORY BUFFER
    # -------------------------
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

        for name, df in kpis.items():
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=name[:31], index=False)

        if qc_summary is not None and not qc_summary.empty:
            qc_summary.to_excel(writer, sheet_name="QC_Summary", index=False)

    # Extract the raw binary data
    excel_data = buffer.getvalue()
    return filename, excel_data


