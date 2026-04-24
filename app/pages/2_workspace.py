import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st
import pandas as pd
from app.components.file_upload import file_uploader_block
from app.components.data_preview import data_preview_block


title_container = st.container()

title_container.title("🚢 Ship Emissions Calculator")
title_container.write("Upload a voyage dataset to begin analysis.")

# ----------------------------
# UPLOAD (always available)
# ----------------------------

file_uploader_block()

# ----------------------------
# READ STATE
# ----------------------------

df = st.session_state.get("df")

if df is None:
    st.info("No dataset loaded yet.")
    st.stop()


data_preview_block(df)





