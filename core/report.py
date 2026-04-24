"""
Report generation utilities.
Produces Excel and CSV summaries from EmissionsResult data.
PDF support can be added via WeasyPrint later.
"""

from __future__ import annotations

import io
import pandas as pd
from .emissions import EmissionsResult


def generate_report(results: list[EmissionsResult], format: str = "xlsx") -> bytes:
    """
    Generate a downloadable report.

    Parameters
    ----------
    results : list[EmissionsResult]
    format  : "xlsx" | "csv"

    Returns
    -------
    bytes - file content ready to serve or write to disk
    """
    rows = [r.to_series() for r in results]
    df = pd.DataFrame(rows)

    # Add totals row
    numeric_cols = df.select_dtypes(include="number").columns
    total = df[numeric_cols].sum()
    total["phase"] = "TOTAL"
    df = pd.concat([df, total.to_frame().T], ignore_index=True)

    if format == "xlsx":
        return _to_excel(df)
    elif format == "csv":
        return df.to_csv(index=False).encode("utf-8")
    else:
        raise ValueError(f"Unsupported format '{format}'. Use 'xlsx' or 'csv'.")


def _to_excel(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Emissions")
        _autofit_columns(writer.sheets["Emissions"])
    return buffer.getvalue()


def _autofit_columns(ws) -> None:
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)
