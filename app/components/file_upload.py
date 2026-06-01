import streamlit as st
import pandas as pd
from pathlib import Path
import json

SUPPORTED_TYPES = ["csv", "xlsx", "xls"]

def load_css():
    css_path = Path(__file__).resolve().parents[1] / "styles" / "style.css"
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    return True

def load_file(file, validator=None):
    """
    Converts uploaded Streamlit file into a pandas DataFrame.
    
    Parameters
    ----------
    file : UploadedFile
        Streamlit uploaded file object.
    validator : callable, optional
        Function that takes a DataFrame and returns (bool, str).
        True = valid, False = invalid with error message.
    """

    if file is None:
        return None

    file_extension = Path(file.name).suffix.lower().replace(".", "")

    if file_extension not in SUPPORTED_TYPES:
        st.error(f"Unsupported file type: .{file_extension}")
        return None

    try:
        if file_extension == "csv":
            df = pd.read_csv(file)
        elif file_extension in ["xlsx", "xls"]:
            df = pd.read_excel(file, engine="openpyxl")
        else:
            return None

        if validator is not None:
            is_valid, message = validator(df)
            if not is_valid:
                st.error(f"File validation failed: {message}")
                return None

        return df

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def data_uploader_block(
    label="Upload your data",
    key="df",
    validator=None
):
    """
    Sets the session state for the key to the data uploaded
    """
    uploaded_file = st.file_uploader(
        label,
        type=SUPPORTED_TYPES,
        key=f"uploader_{key}"  # important: unique widget key
    )

    df = load_file(uploaded_file,validator)

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