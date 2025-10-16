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
            page_tables = page.extract_tables()

            if page_tables:
                for i, table in enumerate(page_tables):
                        if not table or len(table) == 0:
                            continue

                        try:
                            if len(table) > 1:
                                headers = table[0]
                                data = table[1:]
                            else:
                                headers = None
                                data = table

                            # Create DataFrame
                            df = pd.DataFrame(data, columns=headers)

                            # Clean headers and make them unique
                            if headers:
                                clean_headers = []
                                for j, h in enumerate(headers):
                                    if not h or str(h).strip() == '':
                                        clean_headers.append(f"Column_{j}")
                                    else:
                                        clean_headers.append(str(h).strip())
                                df.columns = clean_headers

                            col_count = len(df.columns)
                            # Group tables with same number of columns
                            if col_count not in tables_by_cols:
                                tables_by_cols[col_count] = []
                            tables_by_cols[col_count].append(df)

                        except Exception as e:
                            # Fallback: create without headers
                            try:
                                df = pd.DataFrame(table)
                                col_count = len(df.columns)
                                if col_count not in tables_by_cols:
                                    tables_by_cols[col_count] = []
                                tables_by_cols[col_count].append(df)
                            except:
                                continue              
    
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

        # Display all full tables
        table_count = 0
        for cols, group in tables_by_cols.items():
            st.write(f"## Tables with {cols} columns:")

            for i, df in enumerate(group):
                table_count += 1
                st.write(f"### Table {table_count} (Full)")
                st.write(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
                st.dataframe(df, width="stretch")
