""" 
Using Strealit framework to read a table from a pdf invoice
and display the table with sortable columns 
"""

import streamlit as st
import pdfplumber
import pandas as pd
import numpy as np

st.title('Sortable Tables from Invoices')

st.pdf("Invoice_1479909_e209944.pdf", height=500)

def extract_tables_with_pdfplumber(pdf_path):
    """Extract tables using pdfplumber library"""
    print("=" * 50)
    print("EXTRACTING TABLES WITH PDFPLUMBER")
    print("=" * 50)

    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"\nPage {page_num}:")
            print(f"Page dimensions: {page.width} x {page.height}")

            # Extract text to see content
            text = page.extract_text()
            if text:
                print(f"Text content preview:\n{text[:500]}...")

            # Try to extract tables
            page_tables = page.extract_tables()
            if page_tables:
                print(f"Found {len(page_tables)} table(s) on page {page_num}")
                for i, table in enumerate(page_tables):
                    print(f"\nTable {i+1}:")
                    
                    # Check if table has data
                    if not table or len(table) == 0:
                        print("Empty table, skipping...")
                        continue
                    
                    try:
                        # Handle case where table might not have headers
                        if len(table) > 1:
                            headers = table[0]
                            data = table[1:]
                        else:
                            headers = None
                            data = table
                        
                        # Create DataFrame with error handling
                        df = pd.DataFrame(data, columns=headers)
                        print(df.to_string())
                        tables.append(df)
                        
                    except Exception as e:
                        print(f"Error creating DataFrame for table {i+1}: {e}")
                        # Try creating without headers
                        try:
                            df = pd.DataFrame(table)
                            print(f"Created DataFrame without headers: {df.shape}")
                            tables.append(df)
                        except Exception as e2:
                            print(f"Failed to create DataFrame: {e2}")
                            continue
            else:
                print(f"No tables found on page {page_num}")

    return tables

tables = extract_tables_with_pdfplumber("Invoice_1479909_e209944.pdf")

# Display results
if tables and len(tables) > 0:
    st.write(f"Found {len(tables)} table(s) in the PDF")
    
    # Display each table separately
    for i, df in enumerate(tables):
        st.write(f"## Table {i+1}")
        try:
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error displaying table {i+1}: {e}")
            st.write("Raw table data:")
            st.write(df)
else:
    st.error("No tables were extracted from the PDF")
