import streamlit as st
import datetime as datetime
import pandas as pd

def calls_preview_block(df):
    """
    Streamlit UI block for calls data preview.
    Displays the first few rows and column names of the DataFrame.
    """

    if df is not None:
        total_calls = len(df)
        df["etautc"] = pd.to_datetime(df["etautc"])
        from_date = df["etautc"].min().strftime("%b-%Y")
        to_date = df["etautc"].max().strftime("%b-%Y")


        st.success(f"{total_calls} calls loaded from {from_date} - {to_date}")

        with st.expander("Detected Columns", False):
            st.write(list(df.columns))

def vaixells_preview_block(df):
    """
    Streamlit UI block for vessels data preview.
    Displays the first few rows and column names of the DataFrame.
    """

    if df is not None:
        total_vessels = len(df)

        st.success(f"Information loaded for {total_vessels} vessels.")

        with st.expander("Detected Columns", False):
            st.write(list(df.columns))