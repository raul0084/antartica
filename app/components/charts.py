import streamlit as st
import altair as alt

def emissions_time_chart(df):

    def safe_multiselect(label, column, key):
        """Returns multiselect widget, or hidden empty list if column missing."""
        if column not in df.columns:
            return []
        return st.multiselect(
            label,
            sorted(df[column].dropna().unique().tolist()),
            key=key
        )

    # --- Filters ---
    with st.expander("Filters", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_vessels  = safe_multiselect("Vessel",      "Vessel name", "filter_vessel")
            selected_types    = safe_multiselect("Vessel type",  "Vessel type", "filter_type")

        with col2:
            selected_terminals = safe_multiselect("Terminal",   "Terminal",    "filter_terminal")
            selected_fuels     = safe_multiselect("Fuel type",  "Fuel type",   "filter_fuel")

        with col3:
            selected_esloras   = safe_multiselect("LOA range",  "LOA range",   "filter_eslora")

            pollutants = [c for c in df.columns if c.endswith("total (t)")]
            selected_pollutants = st.multiselect(
                "Pollutant",
                pollutants,
                default=pollutants[:1],
                key="filter_pollutant"
            )

    # --- Apply filters ---
    df_filtered = df.copy()

    if selected_vessels:
        df_filtered = df_filtered[df_filtered["Vessel name"].isin(selected_vessels)]
    if selected_types:
        df_filtered = df_filtered[df_filtered["Vessel type"].isin(selected_types)]
    if selected_terminals:
        df_filtered = df_filtered[df_filtered["Terminal"].isin(selected_terminals)]
    if selected_fuels:
        df_filtered = df_filtered[df_filtered["Fuel type"].isin(selected_fuels)]
    if selected_esloras:
        df_filtered = df_filtered[df_filtered["LOA range"].isin(selected_esloras)]

    # --- Aggregation ---
    if df_filtered.empty:
        st.warning("No data matches the selected filters.")
        return None

    if not selected_pollutants:
        st.info("Select at least one pollutant to display the chart.")
        return None

    df_plot = (
        df_filtered.groupby("Date")[selected_pollutants]
        .sum()
        .reset_index()
        .melt(id_vars="Date", var_name="Pollutant", value_name="Emissions (t)")
    )

    # --- Chart ---
    chart = (
        alt.Chart(df_plot)
        .mark_bar()
        .encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Emissions (t):Q", title="Emissions (t)"),
            color=alt.Color("Pollutant:N"),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Pollutant:N", title="Pollutant"),
                alt.Tooltip("Emissions (t):Q", title="Emissions (tons)", format=".4f")
            ]
        )
        .properties(width="container", height=400)
    )

    st.altair_chart(chart, use_container_width=True)

    return df_filtered
