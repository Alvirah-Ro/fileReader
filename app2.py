""" 
Automated PDF table extractor: Version K
"""

import streamlit as st
import pdfplumber
import pandas as pd
import re

# Import custom functions
from table_functions import fix_concatenated_table, define_headers

st.title('Automated PDF Table Extractor: Version K')

# File uploader for PDF invoice
uploaded_file = st.file_uploader("Upload a PDF invoice", type="pdf")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        all_tables = []

        # DEBUG: page_text = pdf.pages[0].extract_text()
        # DEBUG: st.text_area("Raw text (first 1000 chars):", page_text[:1000])

        for page_num, page in enumerate(pdf.pages, 1): # Start page numbering at 1
            tables = page.extract_tables()
            st.write(f"Found {len(tables)} table(s) on page {page_num}")
            if tables:
                for i, table in enumerate(tables):
                    # DEBUG: st.write(f"DEBUG: Page {page_num}, Table {i + 1}")
                    if st.button(f"Click to see raw data for Table {i + 1} on Page {page_num}", key=f"show_raw_data_{page_num}_{i}", type="secondary"):
                        st.write(f"#### Original Table {i + 1} from Page {page_num}:")
                        st.write(f"Raw: {table}")
                    df = pd.DataFrame(table)
                    st.write(f"#### Original Table {i + 1} from Page {page_num}:")
                    st.dataframe(df, width="stretch")

                    all_tables.append(df)
            else:
                st.warning("No tables detected.  Here's the raw text instead:")


        # Combine all tables
        if all_tables:
            combined_table = pd.concat(all_tables, ignore_index=True)
            df_all = pd.DataFrame(combined_table)
            st.write(f"#### All Tables Combined:")
            st.dataframe(df_all, width="stretch")

        # Fix concatenated data
        if st.button("Fix rows that have been combined", key="fix_concat_btn", type="primary"):
            # Convert DataFrame to list of lists to process
            table_as_list = df_all.values.tolist()

            fixed_table = fix_concatenated_table(table_as_list)
            if fixed_table:
                # On this particular invoice K, the headers are in row fixed_table[3]
                # On this particular invoice K, data does not start until fixed_table[5]
                # TO DO: create a variable for which row to start on 
                # this df is K specific
                # df = pd.DataFrame(fixed_table[5:], columns=fixed_table[3] if fixed_table[3] else None)
                st.write(f"#### Separated data into multiple rows:")
                df = pd.DataFrame(fixed_table, columns=None)
                st.dataframe(df, width="stretch")

        # Choose Headers
        if st.button("Choose which row includeds Headers", key="choose_headers_btn", type="primary"):
            # Convert DataFrame to list of lists to process
            table_as_list = df_all.values.tolist()

            header_row = define_headers(table_as_list)
            if header_row:
                st.write(f"#### These are the headers for the table: {header_row}")
                df = pd.DataFrame(fixed_table, columns=fixed_table[{header_row}])
                st.dataframe(df, width="stretch")

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
