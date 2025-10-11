""" 
Using Strealit framework to read a table from a pdf invoice
and display the table with sortable columns 
"""

import streamlit as st
import pdfplumber
import pandas as pd

st.title('Sortable Tables from Invoices')

# File uploader for PDF invoice
uploaded_file = st.file_uploader("Upload a PDF invoice", type="pdf")

if uploaded_file is not None:
    tables_by_cols = {}
  
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) > 1:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        col_count = len(df.columns)

                        # Group tables with same number of columns
                        if col_count not in tables_by_cols:
                            tables_by_cols[col_count] = []
                        tables_by_cols[col_count].append(df)
    
    if not tables_by_cols:
        st.error("No tables found in the PDF.")
    else:
        # Debug: show what we found
        st.write("**Debug info:**")
        for cols, group in tables_by_cols.items():
            total_rows = sum(len(df) for df in group)
            st.write(f"- {cols} columns: {len(group)} table(s), {total_rows} total rows")

        # Find the group with the most total rows
        biggest_group = max(
        tables_by_cols.values(),
        key=lambda group: sum(len(df) for df in group)
        )

        # Merge all tables in that group
        merged = pd.concat(biggest_group, ignore_index=True)

        # Fix Messy column names
        merged.columns = [
            f"Column_{i}" if not col or pd.isna(col) else col
            for i, col in enumerate(merged.columns)
        ]

        # Remove duplicate header rows
        header_names = list(merged.columns)
        is_header_row = merged.apply(lambda row: list(row) == header_names, axis=1)
        merged = merged[~is_header_row]

        st.success("Tables successfully extracted and merged!")
        st.write("### Merged Table:")
        st.dataframe(merged, width="stretch")

        csv = merged.to_csv(index=False)
        st.download_button("Download CSV", csv, "merged_table.csv")
