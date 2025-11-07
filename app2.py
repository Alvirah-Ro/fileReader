""" 
Automated PDF table extractor: Version K
"""

#To Do: Try Camelot and PDF path to see which one works best for version K


import streamlit as st
import pdfplumber
import pandas as pd
import tabula
import camelot
import re

st.title('Automated PDF Table Extractor: Version K')

# File uploader for PDF invoice
uploaded_file = st.file_uploader("Upload a PDF invoice", type="pdf")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        all_tables = []

        # DEBUG: page_text = pdf.pages[0].extract_text()
        # DEBUG: st.text_area("Raw text (first 1000 chars):", page_text[:1000])

        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) > 1: # Skip empty or single-row tables
                        df = pd.DataFrame(table)
                        all_tables.append(df)

        if all_tables:
            st.success(f"Found {len(all_tables)} table(s) with PDF Plumber")
            st.write(f"### *The original {len(all_tables)} table(s) found on this invoice:")
            for i, df in enumerate(all_tables, 1):
                 st.write(f"#### Table {i} (uncleaned):")
                 st.write(f"Size: {df.shape[0]} rows x {df.shape[1]} columns")
                 st.dataframe(df, width="stretch")
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

    """Extract tables using tabula-py library"""
    # Try to extract all tables from all pages
    tables = tabula.read_pdf(uploaded_file, pages='all', multiple_tables=True)
    all_tables_tab = []
    if tables:
        for table in tables:
            if len(table) > 1: # Skip empty or single-row tables
                df = pd.DataFrame(table)
                all_tables_tab.append(df)
        
    if tables:
        st.success(f"Found {len(all_tables_tab)} table(s) with Tabula")
        st.write(f"The original {len(all_tables_tab)} table(s) found on this invoice:")

        clean_tables_list = []
        for table_index, table in enumerate(all_tables_tab):
                    
            cleaned_rows = []
            # Find headers
            for idx, row in table.iterrows():
                header_row = re.search(r'Qty', str(row.iloc[0]))
                if header_row:
                    st.write(f"We found the word 'Qty' in row index {idx}")
                # DEBUG st.write(f"Row data for row {idx}: {row}")
    


            for i, df in enumerate(all_tables_tab, 1):
                st.write(f"### Table {i}:")
                st.write(f"Size: {df.shape[0]} rows x {df.shape[1]} columns")
                st.dataframe(df, width="stretch")
        
                cleaned_rows = []
                # Try to split data by patterns using numbers as column boundaries
                for idx, row in table.iterrows():
                    st.write(f"Row data for row {idx}: {row}")


        # if clean_tables_list:
        #     combined_clean_table = pd.concat(clean_tables_list, ignore_index=True)
        #     st.write("### All Main Tables Combined:")
        #     st.dataframe(combined_clean_table, width="stretch")


    else:
        st.write("No tables found with tabula")   

    # """Extract tables using camelot library"""    
    # DEBUG - was not working - try again later
    # # Try lattice method first (for tables with clear borders)
    # tables_lattice = camelot.read_pdf(uploaded_file, flavor='lattice', pages='all')

    # all_tables_lattice = []
    # if tables_lattice:
    #     for table in tables_lattice:
    #         if table:
    #             st.write("Tables found")
    #             if len(table) > 1: # Skip empty or single-row tables
    #                 df = pd.DataFrame(table)
    #                 all_tables_lattice.append(df)
    #             else:
    #                 st.write("Table length unknown:", table)
    # if all_tables_lattice:
    #         st.success(f"Found {len(all_tables_lattice)} table(s) with camelot (lattice)")
    #         st.write(f"### The original {len(all_tables_lattice)} table(s) found on this invoice:")
    #         for i, table in enumerate(all_tables_lattice, 1):
    #             st.write(f"### Table {i} (lattice):")
    #             st.dataframe(df, width="stretch")
    # else:
    #     st.warning("No tables detected with Camelot Lattice")            
        
    # # Try stream method (for tables without clear borders)
    # tables_stream = camelot.read_pdf(pdf_path, flavor='stream', pages='all')
            
    # all_tables_stream = []
    # if tables_stream:
    #     for table in tables_stream:
    #         if table and len(table) > 1: # Skip empty or single-row tables
    #             df = pd.DataFrame(table)
    #             all_tables_stream.append(df)
    # if all_tables_lattice:
    #     st.success(f"Found {len(all_tables_stream)} table(s) with camelot (lattice)")
    #     st.write(f"### The original {len(all_tables_stream)} table(s) found on this invoice:")
    #     for i, table in enumerate(all_tables_stream, 1):
    #         st.write(f"### Table {i} (stream):")
    #         st.dataframe(df, width="stretch")
    # else:
    #     st.warning("No tables detected with Camelot Stream")            
