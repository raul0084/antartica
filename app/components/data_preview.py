import streamlit as st
import pandas as pd

def data_preview_block(df):
    """
    Streamlit UI block for data preview.
    Displays the first few rows and column names of the DataFrame.
    """


    if df is not None:

        st.success(f"File uploaded successfully \n (Hint: {df.shape[0]}x{df.shape[1]} matrix)")
        
        with st.expander("📊 Data Preview", False):
            st.dataframe(df.head())

        with st.expander("📌 Detected Columns", False):
            st.write(list(df.columns))
    else:
        st.info("Please upload a file to continue.")

