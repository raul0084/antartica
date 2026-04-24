import streamlit as st
import pandas as pd
from app.components.data_preview import data_preview_block

SUPPORTED_TYPES = ["csv", "xlsx", "xls"]


def load_file(file):
    """
    Converts uploaded Streamlit file into a pandas DataFrame.
    """

    if file is None:
        return None

    file_extension = file.name.split(".")[-1].lower()

    if file_extension not in SUPPORTED_TYPES:
        st.error(f"Unsupported file type: .{file_extension}")
        return None

    try:
        if file_extension == "csv":
            return pd.read_csv(file)

        elif file_extension in ["xlsx", "xls"]:
            return pd.read_excel(file)

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def file_uploader_block(label="Upload your data"):
    uploaded_file = st.file_uploader(label, type=SUPPORTED_TYPES)

    df = load_file(uploaded_file)

    if df is not None:
        st.session_state["df"] = df

    return st.session_state.get("df", None)
