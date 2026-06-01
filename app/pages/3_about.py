import streamlit as st

from app.components.file_upload import load_css

load_css()

def render_about():
    # ── LOAD GLOBAL CSS ─────────────────────────────────────────────
    load_css()

    # ── HERO ───────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero">
            <div class="hero-tag">About Us</div>
            <div class="hero-title">The Team</div>
            <p class="hero-subtitle">
                Our research leader is Marc, he is a ...
                Two bacherlor's theses were developed to fully develop the calculator and ....
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── QUICK STATS ─────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    stats = [
        ("IMO 2023", "Aligned Standard"),
        ("6", "Emission Factors"),
        ("Open Source", "MIT Licensed"),
    ]

    for col, (num, label) in zip([c1, c2, c3], stats):
        col.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">{num}</div>
                <div class="stat-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── MISSION ─────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="mission-block">
            <h2>🌊 Our Mission</h2>
            <p>
                Shipping accounts for roughly <span class="highlight">3% of global greenhouse gas emissions</span>
                and is one of the hardest sectors to decarbonise. Our team is developing
                transparent, peer-reviewed computational tools that allow ports, operators,
                and policymakers to quantify emissions inventories, model
                <span class="highlight">alternative fuels</span>, and evaluate
                pathway scenarios toward IMO's 2050 net-zero target.
                All methods are documented and reproducible.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── TEAM ───────────────────────────────────────────────────────
    st.markdown('<div class="section-label">People</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Research Team</div>', unsafe_allow_html=True)

    team = [
        {
            "initials": "MDC",
            "name": "Dr. Marc Domenech Cerda",
            "role": "Principal Investigator",
            "bio": "TO-DO",
            "tags": ["TO_DO 1", "TO_DO 2", "TO_DO 3"],
        },
        {
            "initials": "RAC",
            "name": "Raúl Ávila Carbajal",
            "role": "Lead Developer",
            "bio": "Responsible for the calculator's core engine and data pipelines.",
            "tags": ["Python", "Data Engineering", "Modelling"],
        },
        {
            "initials": "IDK",
            "name": "Nombre Apellido",
            "role": "PUESTO",
            "bio": "BIO.",
            "tags": ["TO_DO 1", "TO_DO 2", "TO_DO 3"],
        },
        {
            "initials": "IDK",
            "name": "Nombre Apellido",
            "role": "PUESTO",
            "bio": "BIO.",
            "tags": ["TO_DO 1", "TO_DO 2", "TO_DO 3"],
        },
    ]

    cols = st.columns(2, gap="medium")

    for i, member in enumerate(team):
        with cols[i % 2]:
            tags_html = "".join(f'<span class="tag">{t}</span>' for t in member["tags"])

            st.markdown(
                f"""
                <div class="team-card">
                    <div class="team-avatar">{member["initials"]}</div>
                    <p class="team-name">{member["name"]}</p>
                    <p class="team-role">{member["role"]}</p>
                    <p class="team-bio">{member["bio"]}</p>
                    <div class="team-tags">{tags_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── CONTACT ────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Get in Touch</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Contact</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div>
            <span class="contact-pill">✉️ emissions-lab@university.ac.za</span>
            <span class="contact-pill">🐙 github.com/your-org/ship-emissions-calc</span>
            <span class="contact-pill">🌐 university.ac.za/emissions-lab</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Ship Emissions Research Team · 2025")

# ── Standalone run ────────────────────────────────────────────────
if __name__ == "__main__":
    st.set_page_config(
        page_title="About | Ship Emissions Calculator",
        page_icon="🚢",
        layout="wide",
    )
    render_about()