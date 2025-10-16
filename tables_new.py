""" 
More simple automated PDF table extractor
"""

import streamlit as st
import pdfplumber
import pandas as pd

st.title('Automated PDF Table Extractor')

# File uploader for PDF invoice
uploaded_file = st.file_uploader("Upload a PDF invoice", type="pdf")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        all_tables = []

        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) > 1: # Skip empty or single-row tables
                        df = pd.DataFrame(table)
                        all_tables.append(df)

        if all_tables:
            st.success(f"Found {len(all_tables)} table(s)")

            for i, df in enumerate(all_tables, 1):
                st.write(f"### Table {i}")
                st.write(f"Size: {df.shape[0]} rows x {df.shape[1]} columns")
                st.dataframe(df, width="stretch")

                # Download button for each table
                csv = df.to_csv(index=False)
                st.download_button(
                    f"Download Table {i} as CSV",
                    csv,
                    f"table_{i}.csv",
                    key=f"download_{i}"
                )

        else:
            st.warning("No tables detected.  Here's the raw text instead:")

            # Fallback: show text for manual copy/paste
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n\n"

            if full_text:
                st.text_area("Extracted text:", full_text, height=400)
            else:
                st.error("Could not extract any text from this PDF")
