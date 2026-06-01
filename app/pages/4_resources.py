import streamlit as st
import pandas as pd

from app.components.file_upload import load_css
from core.config import default_emission_factors

load_css()

def render_resources():

    # ── HEADER ─────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero">
            <div class="hero-tag">Reference Library</div>
            <div class="hero-title">Resources & References</div>
            <p class="hero-subtitle">
                Curated guidelines, open datasets, regulatory frameworks, and key
                literature underpinning the Ship Emissions Calculator methodology.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── TIP ────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="tip-box">
            <strong>💡 How to use this page:</strong> Use the tabs below to browse by
            category. Each card links directly to the source. Where a DOI is listed, the
            link resolves to the publisher's canonical page. All emission factors used in
            this tool are traceable to one or more sources listed here.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── TABS ───────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📋 Regulations & Standards", "🗄 Datasets", "🛠 Tools & Software",
         "📄 Key Literature", "📐 Emission Factors"]
    )

    # ───────────────────────────────────────────────────────────────
    # TAB 1 — Regulations & Standards
    # ───────────────────────────────────────────────────────────────
    with tab1:
        regs = [
            {
                "icon": "🌐",
                "color": "#e8f5e9",
                "title": "IMO 2023 GHG Strategy",
                "source": "IMO — MEPC 80",
                "badge": ("Regulation", "badge-reg"),
                "desc": "Revised IMO strategy on reduction of GHG emissions from ships.",
                "url": "https://www.imo.org/en/OurWork/Environment/Pages/2023-IMO-Strategy-on-Reduction-of-GHG-Emissions-from-Ships.aspx",
            },
            {
                "icon": "📜",
                "color": "#fce4ec",
                "title": "MARPOL Annex VI",
                "source": "IMO",
                "badge": ("Standard", "badge-std"),
                "desc": "International convention for prevention of air pollution from ships.",
                "url": "https://www.imo.org/en/OurWork/Environment/Pages/Air-Pollution.aspx",
            },
        ]

        

        for r in regs:
            badge_text, badge_class = r["badge"]

            st.markdown(
                f"""
                <div class="res-card">
                    <div class="res-icon" style="background:{r['color']}">{r['icon']}</div>
                    <div class="res-body">
                        <p class="res-title">{r['title']}
                            <span class="res-badge {badge_class}">{badge_text}</span>
                        </p>
                        <p class="res-source">{r['source']}</p>
                        <p class="res-desc">{r['desc']}</p>
                        <a class="res-link" href="{r['url']}" target="_blank">Open →</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ───────────────────────────────────────────────────────────────
    # TAB 2 — Datasets
    # ───────────────────────────────────────────────────────────────

    with tab2:

        for i in range(2012,2027):
            datasets = [
                {
                    "icon": "📊",
                    "color": "#e3f2fd",
                    "title": f"Escalas Puerto Barcelona {i}",
                    "source": "Port de Barcelona",
                    "badge": ("Dataset", "badge-data"),
                    "desc": "Comprehensive dataset of vessels that have made port calls at the Port of Barcelona.",
                    "url": f"app/data/emissions_tools/escalas_finalizadas_{i}.csv",
                },
        ]

        for d in datasets:
            badge_text, badge_class = d["badge"]

            st.markdown(
                f"""
                <div class="res-card">
                    <div class="res-icon" style="background:{d['color']}">{d['icon']}</div>
                    <div class="res-body">
                        <p class="res-title">{d['title']}
                            <span class="res-badge {badge_class}">{badge_text}</span>
                        </p>
                        <p class="res-source">{d['source']}</p>
                        <p class="res-desc">{d['desc']}</p>
                        <a class="res-link" href="{d['url']}" target="_blank">Download →</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ───────────────────────────────────────────────────────────────
    # TAB 5 — Emission Factors (unchanged but cleaner)
    # ───────────────────────────────────────────────────────────────
    with tab5:
        st.markdown('<div class="section-label">Quick Reference</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Default Emission Factors</div>', unsafe_allow_html=True)

        EF_custom_json = default_emission_factors()

        rows = []

        for fuel, fuel_data in EF_custom_json.items():
            # Skip metadata and defaults
            if fuel.startswith("_") or fuel == "defaults":
                continue

            for engine_type, values in fuel_data.items():
                row = {
                    "fuel": fuel,
                    "engine": engine_type,
                    **values  # unpack pollutants
                }
                rows.append(row)

        EF_custom = pd.DataFrame(rows)

        st.dataframe(EF_custom, use_container_width=True, hide_index=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label">Formula</div>', unsafe_allow_html=True)
        st.latex(r"E_i = \sum_j FC_j \times EF_{i,j}")

    st.caption("Last updated: June 2025 · Ship Emissions Research Team")


# ── Standalone run ────────────────────────────────────────────────
if __name__ == "__main__":
    st.set_page_config(
        page_title="Resources | Ship Emissions Calculator",
        page_icon="🚢",
        layout="wide",
    )
    render_resources()