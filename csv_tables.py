import streamlit as st
import pandas as pd

st.title("CSV Table Viewer")

uploaded_file = st.file_uploader("Upload CSV File", type="csv")

if uploaded_file is not None:
    # Read the CSV
    df = pd.read_csv(uploaded_file)

    st.write(f"**Table Info:** {len(df)} rows x {len(df.columns)} columns")

    #Display the table
    st.dataframe(df, width="stretch")

    st.write("**Columns:**", list(df.columns))
