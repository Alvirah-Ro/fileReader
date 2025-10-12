""" 
Using Strealit framework to read a table from a pdf invoice
and display the table with sortable columns 
"""

import streamlit as st
import pdfplumber
import pandas as pd

def split_invoice_columns(df):
    """Split single column data into proper columns"""
    if len(df.columns) == 1:
        col_name = df.columns[0]

        # Split each row by 2 or more spaces
        split_rows = []
        for value in df[col_name]:
            if pd.isna(value):
                # Split by 2+ spaces
                parts = [p.strip() for p in str(value).split('  ') if p.strip()]
                if parts: # Only keep non-empty splits
                    split_data.append(parts)
        
        if not split_rows:
            return df

        # Find maximum number of columns and then pad rows
        max_cols = max(len(row) for row in split_rows)
        padded_rows = [row + [''] * (max_cols - len(row)) for row in split_rows]

        # Use invoice column names
        headers = ['Edition', 'Location', 'Title', 'Order', 'Ship', 'BO', 'List', 'Disc', 'New', 'Extension']
        column_names = headers[:max_cols] + [f'Col_{i}' for i in range(max_cols - len(headers))]

        return pd.DataFrame(padded_rows, columns=column_names[:max_cols])
    
    return df

st.title('Sortable Tables from Invoices')

# File uploader for PDF invoice
uploaded_file = st.file_uploader("Upload a PDF invoice", type="pdf")

if uploaded_file:
    all_tables = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) >1:
                        # Create DataFrame and clean it
                            df = pd.DataFrame(table[1:], columns=table[0])
                            df = split_invoice_columns(df)
                            all_tables.append(df)

    if not all_tables:
        st.error("No tables found")
    else:
        # Show all tables
        for i, df in enumerate(all_tables, 1):
            st.write(f"### Table {i}")
            st.write(f"Shape: {df.shape}")
            st.dataframe(df)


        # # Debug: show what we found
        # st.write("**Debug info:**")
        # for cols, group in tables_by_cols.items():
        #     total_rows = sum(len(df) for df in group)
        #     st.write(f"- {cols} columns: {len(group)} table(s), {total_rows} total rows")

        #     for i, df in enumerate(group):
        #         st.write(f" Table {i+1} preview (first 3 rows):")
        #         st.dataframe(df.head(3))
        #         st.write(f" Column Names: {list(df.columns)}")

        # # Display all full tables
        # table_count = 0
        # for cols, group in tables_by_cols.items():
        #     st.write(f"## Tables with {cols} columns:")

        #     for i, df in enumerate(group):
        #         table_count += 1
        #         st.write(f"### Table {table_count} (Full)")
        #         st.write(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        #         st.dataframe(df, width="stretch")
