"""
Streamlit frontend for the Ship Emissions Calculator.
Communicates with the FastAPI backend via HTTP.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import io, os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Ship Emissions Calculator",
    page_icon="🚢",
    layout="wide",
)

st.title("🚢 Ship Emissions Calculator")
st.caption("Upload a voyage file to calculate emissions across all operational phases.")

with st.expander("📄 Expected file format"):
    st.markdown("""
    Your CSV or Excel file must contain these columns:

    | Column | Description | Example |
    |--------|-------------|---------|
    | `phase` | Voyage phase name | At-Sea |
    | `duration_h` | Duration (hours) | 48 |
    | `load_factor` | Engine load 0–1 | 0.75 |
    | `engine_name` | Engine label | Main Engine |
    | `power_kw` | Installed power (kW) | 12000 |
    | `sfc_g_per_kwh` | Specific fuel consumption | 175 |
    | `fuel_type` | HFO / MDO / LNG / VLSFO | HFO |
    | `num_units` | Number of identical engines | 1 |

    Each row = one engine in one phase. Multiple engines in the same phase share the same phase/duration/load_factor.
    """)

uploaded = st.file_uploader("Upload voyage file (CSV or Excel)", type=["csv", "xlsx"])

if uploaded:
    if st.button("▶ Calculate Emissions", type="primary"):
        with st.spinner("Running emissions model..."):
            try:
                resp = requests.post(
                    f"{API_URL}/calculate",
                    files={"file": (uploaded.name, uploaded.getvalue())},
                )
                if resp.ok:
                    st.session_state["results"] = pd.DataFrame(resp.json())
                    st.session_state["file_bytes"] = uploaded.getvalue()
                    st.session_state["file_name"] = uploaded.name
                else:
                    st.error(f"Model error: {resp.json().get('detail')}")
            except requests.ConnectionError:
                st.error(f"Cannot reach API at {API_URL}. Is the backend running?")

if "results" in st.session_state:
    df = st.session_state["results"]

    st.divider()
    st.subheader("📊 Results Summary")

    # KPI row
    total_row = df[df["phase"] == "TOTAL"].iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Fuel Consumed", f"{total_row['fuel_consumption_kg']:,.0f} kg")
    col2.metric("Total CO₂e", f"{total_row['co2_equivalent_kg']:,.0f} kg")
    col3.metric("Total CO₂", f"{total_row['CO2_kg']:,.0f} kg")

    st.dataframe(df, use_container_width=True)

    st.subheader("📈 CO₂ Equivalent by Phase")
    chart_df = df[df["phase"] != "TOTAL"]
    fig = px.bar(
        chart_df,
        x="phase",
        y="co2_equivalent_kg",
        color="phase",
        labels={"co2_equivalent_kg": "CO₂e (kg)", "phase": "Voyage Phase"},
        title="CO₂-equivalent emissions per operational phase",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🧪 Pollutant Breakdown (TOTAL)")
    pollutant_cols = [c for c in df.columns if c.endswith("_kg") and c not in ("fuel_consumption_kg", "co2_equivalent_kg")]
    pollutant_data = total_row[pollutant_cols].rename(lambda x: x.replace("_kg", ""))
    fig2 = px.bar(
        x=pollutant_data.index,
        y=pollutant_data.values,
        labels={"x": "Pollutant", "y": "kg"},
        title="Total emissions by pollutant",
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("⬇ Download Report")
    fmt = st.selectbox("Format", ["xlsx", "csv"])
    dl_resp = requests.post(
        f"{API_URL}/report?format={fmt}",
        files={"file": (st.session_state["file_name"], st.session_state["file_bytes"])},
    )
    if dl_resp.ok:
        st.download_button(
            label=f"Download emissions_report.{fmt}",
            data=dl_resp.content,
            file_name=f"emissions_report.{fmt}",
        )