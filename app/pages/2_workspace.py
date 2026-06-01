import streamlit as st

from app.components.file_upload import data_uploader_block, upload_emission_factors, upload_uncertainties, load_css
from app.components.data_preview import calls_preview_block, vaixells_preview_block
from app.components.charts import emissions_time_chart
from core.pipeline import run_pipeline
from core.config import default_uncertainties, default_emission_factors, validate_calls, validate_vaixells
from core.report import generate_excel_report

st.set_page_config(layout="wide")

load_css()

title_container = st.container()

title_container.markdown("""
                        <div class="hero">
                            <div class="hero-tag">Workspace</div>
                            <div class="hero-title">Emissions Tracker</div>
                            <div class="hero-subtitle">Upload, analyze, and download your emissions data</div>
                        </div>
                        """,
                        unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

main_col, right_col = st.columns([3, 1])

with right_col:

        with st.expander("Upload Data", expanded=True):
            st.subheader("Main Data Inputs")

            # UPLOAD PORT CALLS
            df_calls =data_uploader_block(key="calls", validator=validate_calls)
            calls_preview_block(df_calls)

            # UPLOAD VESSEL INFO
            df_vaixells = data_uploader_block(key="vaixells", validator=validate_vaixells)
            vaixells_preview_block(df_vaixells) 

            if st.button("🔄 Reset", key="btn_reset_sys_variables"):
                st.session_state.clear()
                st.rerun()

            st.subheader("Optional Data Inputs")

            # LOADING EMISSION FACTORS & UNCERTAINTIES
            EF_custom = upload_emission_factors()
            U_custom = upload_uncertainties()

            # Use custom if uploaded, otherwise pipeline loads defaults internally
            EF = EF_custom if EF_custom is not None else default_emission_factors()
            U = U_custom if U_custom is not None else default_uncertainties()
              
with main_col:

    if df_calls is None and df_vaixells is None:
        st.markdown(
            """
            <div class="tip-box">
                <strong>💡 Upload both datasets to continue.</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()
    elif df_vaixells is None:
        st.markdown(
            """
            <div class="tip-box">
                <strong>💡 Upload vessels dataset to continue.</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()
    elif df_calls is None:
        st.markdown(
            """
            <div class="tip-box">
                <strong>💡 Upload port calls dataset to continue.</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()
    else: 
        data_ready = True

    if data_ready:
        with st.spinner("Running model..."):
            df_results, kpis, df_unmatched = run_pipeline(df_calls, df_vaixells, EF, U)

        st.session_state["results"] = df_results
        st.session_state["kpis"] = kpis
        st.session_state["unmatched"] = df_unmatched

    if not df_unmatched.empty:
        st.warning(f"{len(df_unmatched)} port calls could not be matched to a vessel and used default values.")
        with st.expander("View unmatched calls"):
            st.dataframe(df_unmatched)

    if "results" in st.session_state:
        df_filtered = emissions_time_chart(st.session_state["results"])

        col1, col2= st.columns([1, 1])

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

            

    

    

