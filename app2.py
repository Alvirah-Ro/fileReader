""" 
Automated PDF table extractor: Version K
"""

import streamlit as st
import pdfplumber
import pandas as pd
import re

st.title('Automated PDF Table Extractor: Version K')

# File uploader for PDF invoice
uploaded_file = st.file_uploader("Upload a PDF invoice", type="pdf")

if st.button("Click Me"):
    st.write("You clicked the button!")

def fix_concatenated_table(table):
    """Fix tables where PDFPlumber concatenates column data"""
    if  not table or len(table) < 2:
        return table
                
    fixed_rows = []
    # Process each row
    for row in table:
        # Split each cell by newlines to get individual values
        split_cells = []
        max_items = 0 # Start at 0 to find out how many separate rows we need to create

        for cell in row:
            if cell: # Convert everything to string, then split
                items = [item.strip() for item in str(cell).split('\n') if item.strip()]
                split_cells.append(items)
                max_items = max(max_items, len(items)) # Update if this cell has more items
            else:
                split_cells.append(['']) # Handle None/Empty cells

        # Create individual rows from split data
        for idx in range(max_items):
            new_row = []
            for cell_items in split_cells:
                if idx < len(cell_items):
                    new_row.append(cell_items[idx])
                else:
                    new_row.append('')
            fixed_rows.append(new_row)
                        
    return fixed_rows


if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        all_tables = []

        # DEBUG: page_text = pdf.pages[0].extract_text()
        # DEBUG: st.text_area("Raw text (first 1000 chars):", page_text[:1000])

        for page_num, page in enumerate(pdf.pages, 1): # Start page numbering at 1
            tables = page.extract_tables()
            st.write(f"Found {len(tables)} tables on page {page_num}")
            if tables:
                for i, table in enumerate(tables):
                    st.write(f"DEBUG: Page {page_num}, Table {i + 1}")
                    st.write(f"\nOriginal Table {i + 1} from Page {page_num}:")
                    st.write(f"Raw: {table}")
                    df = pd.DataFrame(table)
                    st.write(f"Original Table {i + 1} from Page {page_num}:")
                    st.dataframe(df, width="stretch")

                    if st.button("Fix rows that have been combined",key="fix_btn_{page_num}_{i}"):
                        # Fix concatenated data
                        fixed_table = fix_concatenated_table(table)

                        st.write(f"Fixed Table {i + 1} from Page {page_num}:")
                        if fixed_table:
                            # On this particular invoice, the headers are in row fixed_table[3]
                            # On this particular invoice, data does not start until fixed_table[5]
                            # TO DO: create a variable for which row to start on 
                            df = pd.DataFrame(fixed_table[5:], columns=fixed_table[3] if fixed_table[3] else None)
                            st.dataframe(df, width="stretch")
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
