import streamlit as st
import pandas as pd
from pathlib import Path
import json

SUPPORTED_TYPES = ["csv", "xlsx", "xls"]

def load_file(file):
    """
    Converts uploaded Streamlit file into a pandas DataFrame.
    """

    if file is None:
        return None

    file_extension = Path(file.name).suffix.lower().replace(".", "")

    if file_extension not in SUPPORTED_TYPES:
        st.error(f"Unsupported file type: .{file_extension}")
        return None

    try:
        if file_extension == "csv":
            return pd.read_csv(file)

        elif file_extension in ["xlsx", "xls"]:
            return pd.read_excel(file, engine="openpyxl")

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def data_uploader_block(
    label="Upload your data",
    key="df"
):
    """
    Sets the session state for the key to the data uploaded
    """
    uploaded_file = st.file_uploader(
        label,
        type=SUPPORTED_TYPES,
        key=f"uploader_{key}"  # important: unique widget key
    )

    df = load_file(uploaded_file)

    if df is not None:
        st.session_state[key] = df

    return st.session_state.get(key, None)

def upload_emission_factors(key="EF"):
    uploaded_file = st.file_uploader(
        "Upload Emission Factors (Optional)",
        type=["json"],
        key=f"{key}_upload"  # was hardcoded "EF_upload"
    )
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state[key] = data
            st.success("Emission factors updated from file")
            return st.session_state.get(key, None)
        except Exception as e:
            st.error(f"Invalid EF file: {e}")


def upload_uncertainties(key="U"):
    uploaded_file = st.file_uploader(
        "Upload Uncertainties (Optional)",
        type=["json"],
        key=f"{key}_upload"  # was hardcoded "U_upload"
    )
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state[key] = data
            st.success("Uncertainties updated from file")
            return st.session_state.get(key, None)
        except Exception as e:
            st.error(f"Invalid uncertainty file: {e}")