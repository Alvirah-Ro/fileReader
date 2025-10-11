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
            # Try multiple extraction strategies
            strategies = [
                {"vertical_strategy": "text", "horizontal_strategy": "text"},
                {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
                {"vertical_strategy": "text", "snap_tolerance": 5},
                # Explicit columns based on your invoice layout
                {
                    "explicit_vertical_lines": [72, 120, 200, 350, 380, 410, 440, 470, 500, 530],
                    "snap_tolerance": 3
                }
            ]

            best_tables = []
            max_cols = 0

            for strategy in strategies:
                try:
                    tables = page.extract_tables(table_settings=strategy)
                    if tables:
                        for table in tables:
                            if table and len(table) > 1:
                                max_table_cols = max(len(row) for row in table)
                                if max_table_cols > max_cols:
                                    max_cols = max_table_cols
                                    best_tables = tables
                except Exception as e:
                    print (f"Strategy failed: {e}")
                    continue

            # Use the best extraction
            tables = best_tables or page.extract_tables()

            if tables:
                for table in tables:
                    if table and len(table) >1:
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

        for i, df in enumerate(group):
            st.write(f" Table {i+1} preview (first 3 rows):")
            st.dataframe(df.head(3))
            st.write(f" Column Names: {list(df.columns)}")

        table_count = 0
        for cols, group in tables_by_cols.items():
            st.write(f"## Tables with {cols} columns:")

            for i, df in enumerate(group):
                table_count += 1
                st.write(f"### Table {table_count}")
                st.write(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")

            # Fix Messy column names
            df.columns = [
                f"Column_{j}" if not col or pd.isna(col) else col
                for j, col in enumerate(df.columns)
            ]

            # Display the table
            st.dataframe(df, width="stretch")
