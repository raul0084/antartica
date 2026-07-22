"""
Streamlit page: single-voyage emissions simulation.

Two ways to get a route:
  A) Upload an existing GPX (e.g. a planned or logged Antarctic track)
  B) Manually enter waypoints in an editable table

Either way you get: distance (nm) -> nav_time (h) via cruising speed,
a map preview, and a GPX download of whatever route is currently loaded.

Drop this in your app's `pages/` folder (rename with whatever number
prefix fits your existing page order) and adjust the `from core...`
imports to match your package layout.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk

from app.components.file_upload import load_css
from core.simulation import run_single_voyage, summarize_voyage
from core.gpx_utils import parse_gpx, route_distance_nm, estimate_nav_time, build_gpx
from core.config import default_emission_factors, default_uncertainties
from core.report import generate_excel_report

st.set_page_config(layout="wide")
load_css()

title_container = st.container()

title_container.markdown("""
                        <div class="hero">
                            <div class="hero-tag">Simulation</div>
                            <div class="hero-title">Single-Voyage Emissions Simulation</div>
                            <div class="hero-subtitle">Plan a route and simulate emissions</div>
                        </div>
                        """,
                        unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

EF = default_emission_factors()
U = default_uncertainties()
fuel_options = sorted(k for k, v in EF.items() if isinstance(v, dict))

# -------------------------------------------------------------------
# SESSION STATE
# -------------------------------------------------------------------
if "route_points" not in st.session_state:
    st.session_state.route_points = pd.DataFrame(columns=["lat", "lon"])
if "nav_time_override" not in st.session_state:
    st.session_state.nav_time_override = None


def render_route_map(points_df: pd.DataFrame):
    path_layer = pdk.Layer(
        "PathLayer",
        data=[{"path": points_df[["lon", "lat"]].values.tolist()}],
        get_path="path",
        get_width=3,
        width_min_pixels=2,
        get_color=[0, 120, 200],
    )
    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=points_df,
        get_position="[lon, lat]",
        get_radius=8000,
        get_fill_color=[200, 30, 0],
    )
    view_state = pdk.ViewState(
        latitude=points_df["lat"].mean(),
        longitude=points_df["lon"].mean(),
        zoom=2,
    )
    st.pydeck_chart(pdk.Deck(layers=[path_layer, point_layer], initial_view_state=view_state))

# =====================================================================
# TAB 1: VESSEL SPECS + TIMES -> RUN SIMULATION
# =====================================================================

tab_vessel, tab_route = st.tabs(["1. Vessel & Times", "2. Route"])

with tab_vessel:
    st.subheader("Vessel specification")

    col1, col2, col3 = st.columns(3)
    with col1:
        voyage_date = st.date_input("Voyage date")
        fuel = st.selectbox("Fuel type", fuel_options)
        eslora_metres = st.number_input("LOA (m)", min_value=0.0, value=100.0)
    with col2:
        p_main = st.number_input("Main engine power (kW)", min_value=0.0, value=10000.0)
        p_aux = st.number_input("Aux engine power (kW)", min_value=0.0, value=2000.0)
    with col3:
        p_gt = st.number_input("Gross tonnage (GT)", min_value=0.0, value=5000.0)

    with st.expander("Load factors (advanced — defaults match the batch pipeline)"):
        lf_col1, lf_col2, lf_col3, lf_col4 = st.columns(4)
        lf_main = lf_col1.number_input("LF main", 0.0, 1.0, 0.2)
        lf_aux_nav = lf_col2.number_input("LF aux (nav)", 0.0, 1.0, 0.2)
        lf_aux_mani = lf_col3.number_input("LF aux (mani)", 0.0, 1.0, 0.5)
        lf_aux_hot = lf_col4.number_input("LF aux (hotelling)", 0.0, 1.0, 0.4)

    st.subheader("Operational times (hours)")
    t_col1, t_col2, t_col3 = st.columns(3)

    nav_default = st.session_state.nav_time_override or 1.0
    with t_col1:
        nav_time = st.number_input(
            "Navigation time",
            min_value=0.0,
            value=float(nav_default),
            help="Overwritten by 'Use this navigation time' in tab 1 if you clicked it.",
        )
    with t_col2:
        mani_time = st.number_input("Manoeuvring time", min_value=0.0, value=1.6)
    with t_col3:
        hot_time = st.number_input("Hotelling time", min_value=0.0, value=8.0)

    if st.button("Run simulation", type="primary"):
        inputs = {
            "p_main": p_main, "p_aux": p_aux, "p_gt": p_gt,
            "fuel": fuel, "eslora_metres": eslora_metres,
            "nav_time": nav_time, "mani_time": mani_time, "hot_time": hot_time,
            "lf_main": lf_main, "lf_aux_nav": lf_aux_nav,
            "lf_aux_mani": lf_aux_mani, "lf_aux_hot": lf_aux_hot,
            "voyage_date": voyage_date,
        }
        try:
            result_df = run_single_voyage(inputs, EF, U)
            summary_df = summarize_voyage(result_df)

            st.subheader("Results")
            st.dataframe(summary_df, use_container_width=True)
            st.bar_chart(summary_df.set_index("Pollutant")["Emissions (t)"])

            _, excel_bytes = generate_excel_report(
                result_df,
                kpis={"Voyage_Detail": result_df, "Summary": summary_df},
            )
            st.download_button(
                "Download Excel report",
                data=excel_bytes,
                file_name="voyage_simulation.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except ValueError as e:
            st.error(str(e))

# =====================================================================
# TAB 2: ROUTE (GPX upload or manual waypoints)
# =====================================================================

with tab_route:
    st.subheader("Define the route")
    mode = st.radio("Route source", ["Upload GPX", "Enter waypoints manually"], horizontal=True)

    if mode == "Upload GPX":
        gpx_file = st.file_uploader("Upload a .gpx file", type=["gpx"])
        if gpx_file is not None:
            try:
                st.session_state.route_points = parse_gpx(gpx_file)
                st.success(f"Loaded {len(st.session_state.route_points)} points from GPX.")
            except ValueError as e:
                st.error(str(e))

    else:
        st.caption("Add waypoints in order (lat/lon, decimal degrees). Use the + row to add more.")
        edited = st.data_editor(
            st.session_state.route_points[["lat", "lon"]]
            if not st.session_state.route_points.empty
            else pd.DataFrame({"lat": [], "lon": []}),
            num_rows="dynamic",
            use_container_width=True,
            key="waypoint_editor",
        )
        st.session_state.route_points = edited.dropna()

    points_df = st.session_state.route_points

    if len(points_df) >= 2:
        distance_nm = route_distance_nm(points_df)
        st.metric("Route distance", f"{distance_nm:,.1f} nm")

        render_route_map(points_df)

        speed_kn = st.number_input("Cruising speed (knots)", min_value=0.1, value=12.0, step=0.5)
        computed_nav_time = estimate_nav_time(distance_nm, speed_kn)
        st.write(f"Estimated navigation time: **{computed_nav_time:,.2f} h**")

        if st.button("Use this navigation time in the simulation"):
            st.session_state.nav_time_override = computed_nav_time
            st.success(f"nav_time set to {computed_nav_time:,.2f} h — see tab 1.")

        gpx_bytes = build_gpx(points_df, name="simulated_voyage")
        st.download_button(
            "Download route as GPX",
            data=gpx_bytes,
            file_name="simulated_voyage.gpx",
            mime="application/gpx+xml",
        )
    elif len(points_df) == 1:
        st.info("Add at least one more point to compute a distance.")
        render_route_map(points_df)

