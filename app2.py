""" 
Automated PDF table extractor: Version K
"""

import streamlit as st
import pdfplumber
import pandas as pd
import re

# Import custom functions
from table_functions import fix_concatenated_table, clean_duplicate_headers

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
                    if st.button(f"Click to see raw data for Table {i + 1} on Page {page_num}", 
                                 key=f"show_raw_data_{page_num}_{i}", type="secondary"):
                        st.write(f"#### Original Table {i + 1} from Page {page_num}:")
                        st.write(f"Raw: {table}")
                    df = pd.DataFrame(table)
                    if st.button(f"Click to see original Table {i + 1} from Page {page_num}",
                                 key=f"show_original_table_{page_num}_{i}", type="secondary"):
                        st.write(f"#### Original Table {i + 1} from Page {page_num}:")
                        st.dataframe(df, width="stretch")
                    all_tables.append(df)
            else:
                st.warning("No tables detected.  Here's the raw text instead:")


        # Combine all tables and initialize session state
        if all_tables and 'main_table' not in st.session_state:
            combined_table = pd.concat(all_tables, ignore_index=True)
            st.session_state.main_table = combined_table
            # Convert dataframe to list of lists for processing
            st.session_state.table_as_list = combined_table.values.tolist()
            st.session_state.current_headers = None
            st.success("Main table initialized!")

        # Display current main table
        if 'main_table' in st.session_state:
            st.write(f"### All Tables Combined:")
            st.write(f"#### Current Main Table:")
            st.write("Click on options below to format table")
            st.dataframe(st.session_state.main_table, width="stretch")

        # Fix concatenated data
        if st.button("Fix rows that have been combined", key="fix_concat_btn", type="primary"):
            if 'table_as_list' in st.session_state:
                fixed_table = fix_concatenated_table(st.session_state.table_as_list)
                if fixed_table:
                    # Check if current_headers exists and is not None
                    headers_to_use = None
                    if 'current_headers' in st.session_state and st.session_state.current_headers is not None:
                        headers_to_use = st.session_state.current_headers
                    # On this particular invoice K, the headers are in row fixed_table[3]
                    # On this particular invoice K, data does not start until fixed_table[5]
                    # TO DO: create a variable for which row to start on 
                    # this df is K specific
                    # df = pd.DataFrame(fixed_table[5:], columns=fixed_table[3] if fixed_table[3] else None)
                    st.session_state.main_table = pd.DataFrame(fixed_table, columns=headers_to_use)
                    st.session_state.table_as_list = fixed_table
                    st.success(f"Table rows have been separated!")
                    st.rerun() # Refresh to show changes
            else:
                st.error("No table data available to fix")

        # Number input for choosing headers
        st.write("#### Choose Header Row")
        header_row_input = st.number_input("Select the first row that includes headers",
                                            min_value=0, 
                                            max_value=len(st.session_state.table_as_list) - 1 if 'table_as_list' in st.session_state else 10,
                                            value=0,
                                            key="header_row_selector")
        
        # Row input for data start
        data_start_input = st.number_input("Select the first row that contains actual data",
                                           min_value=header_row_input + 1,
                                           max_value=len(st.session_state.table_as_list),
                                           value=header_row_input + 1,
                                           key="data_start_selector")

        # Choose Headers
        if st.button("Click to Apply Headers and Data Start", key="choose_headers_btn", type="primary"):
            if 'table_as_list' in st.session_state:
                header_row = header_row_input
                data_start_row = data_start_input
                st.write(f"#### Headers found in row: {header_row}, Data starts at row: {data_start_row}")
                
                # Create new dataframe with headers
                fixed_data = st.session_state.table_as_list
                if len(fixed_data) > data_start_row:
                    raw_headers = fixed_data[header_row]

                    # Clean duplicate headers
                    clean_headers = clean_duplicate_headers(raw_headers)

                    # Store headers in session state
                    st.session_state.current_headers = clean_headers
                    st.session_state.raw_headers = raw_headers
                    st.session_state.header_row_index = header_row
                    st.session_state.data_start_index = data_start_row

                    #DEBUG:
                    if raw_headers != clean_headers:
                        st.write("**Original headers:**", raw_headers)
                        st.write("**Cleaned headers:**", clean_headers)

                    data = fixed_data[data_start_row:] # Use custom data start row

                    try:
                        st.session_state.main_table = pd.DataFrame(data, columns=clean_headers)
                        st.success(f"Headers applied from row {header_row}, data starts at row {data_start_row}!")
                        st.rerun()
                    except ValueError as e:
                        st.error(f"Error creating DataFrame: {e}")
                        st.write("Raw headers:", raw_headers)
                        st.write("Cleaned headers:", clean_headers)
                        st.write(f"Number of headers: {len(clean_headers)}")
                        st.write(f"Number of data columns: {len(data[0]) if data else 0}")
                else:
                    st.error(f"Not enough data at row {data_start_row}")
            else:
                st.error("Could not find headers in the table")

        # Reset button to start over
        if st.button("Reset to Original", key="reset_btn", type="secondary"):
            if all_tables:
                combined_table = pd.concat(all_tables, ignore_index=True)
                st.session_state.main_table = combined_table
                st.session_state.table_as_list = combined_table.values.tolist()

                # Clear header session state variables
                if 'current_headers' in st.session_state:
                    del st.session_state.current_headers
                if 'raw_headers' in st.session_state:
                    del st.session_state.raw_headers
                if 'header_row_index' in st.session_state:
                    del st.session_state.header_row_index

                st.success("Table reset to original!")
                st.rerun()

    # Fallback: show text for manual copy/paste
    if not all_tables:
        full_text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n\n"

        if full_text:
            st.text_area("Extracted text:", full_text, height=400)
        else:
            st.error("Could not extract any text from this PDF")

# Clear session state when new file is uploaded
if uploaded_file is None and 'main_table' in st.session_state:
    del st.session_state.main_table
    del st.session_state.table_as_list
