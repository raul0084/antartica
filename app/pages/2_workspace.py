import streamlit as st

from app.components.file_upload import data_uploader_block, upload_emission_factors, upload_uncertainties
from app.components.data_preview import calls_preview_block, vaixells_preview_block
from app.components.charts import emissions_time_chart
from core.pipeline import run_pipeline
from core.config import default_uncertainties, default_emission_factors, validate_calls, validate_vaixells
from core.report import generate_excel_report

st.set_page_config(layout="wide")

left_col, main_col = st.columns([1, 3])

with left_col:

    st.subheader("Main Data Inputs")

    # UPLOAD PORT CALLS
    df_calls =data_uploader_block(key="calls", validator=validate_calls)
    calls_preview_block(df_calls)

    # UPLOAD VESSEL INFO
    df_vaixells = data_uploader_block(key="vaixells", validator=validate_vaixells)
    vaixells_preview_block(df_vaixells) 

    st.subheader("Optional Data Inputs")

    # LOADING EMISSION FACTORS & UNCERTAINTIES
    EF_custom = upload_emission_factors()
    U_custom = upload_uncertainties()

    # Use custom if uploaded, otherwise pipeline loads defaults internally
    EF = EF_custom if EF_custom is not None else default_emission_factors()
    U = U_custom if U_custom is not None else default_uncertainties()

              
with main_col:

    title_container = st.container()
    st.title("🚢 Ship Emissions Calculator")

    if df_calls is None and df_vaixells is None:
        st.info("Upload both datasets to continue.")
        st.stop()
    elif df_vaixells is None:
        st.info("Upload vessels dataset to continue.")
        st.stop()
    elif df_calls is None:
        st.info("Upload port calls dataset to continue.")
        st.stop()
    else: 
        st.info("Both datasets loaded, you are ready to go.")
        data_ready = True

    if data_ready:
        with st.spinner("Running model..."):
            df_results, kpis = run_pipeline(df_calls, df_vaixells, EF, U)

        st.session_state["results"] = df_results
        st.session_state["kpis"] = kpis

    if "results" in st.session_state:
        df_filtered = emissions_time_chart(st.session_state["results"])

        col1, col2 = st.columns([1, 1])

        with col1:
            filename, excel_bytes = generate_excel_report(st.session_state["results"])
            st.download_button(
                label="📥 Download Emissions Report",
                data=excel_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_download_full"
            )

        with col2:
            if df_filtered is not None:
                filename_filtered, excel_bytes_filtered = generate_excel_report(df_filtered)
                st.download_button(
                    label="📥 Download Filtered Report",
                    data=excel_bytes_filtered,
                    file_name=f"filtered_{filename_filtered}",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="btn_download_filtered"
                )

    

    

