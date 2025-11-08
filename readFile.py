import streamlit as st
import pdfplumber
import pandas as pd
import tabula
import camelot
from PyPDF2 import PdfReader
import os

st.title('Testing Different PDF Table Extraction Methods')


# File uploader for PDF invoice
uploaded_file = st.file_uploader("Upload a PDF invoice", type="pdf")


def extract_tables_with_pdfplumber(uploaded_file):
    """Extract tables using pdfplumber library"""
    st.write("=" * 50)
    st.write("EXTRACTING TABLES WITH PDFPLUMBER")
    st.write("=" * 50)

    tables = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            st.write(f"\nPage {page_num}:")
            st.write(f"Page dimensions: {page.width} x {page.height}")

            # Extract text to see content
            text = page.extract_text()
            if text:
                st.write(f"Text content preview:\n{text[:500]}...")

            # Try to extract tables
            page_tables = page.extract_tables()
            if page_tables:
                st.write(f"Found {len(page_tables)} table(s) on page {page_num}")
                for i, table in enumerate(page_tables):
                    st.write(f"\nTable {i+1}:")
                    st.write(f"Raw table {i}:")
                    for row_idx, row in enumerate(tables):
                        st.write(f"Row {row_idx}: {row}")
                    if table and len(table) > 1:
                        df = pd.DataFrame(table)
                    else:
                        df = pd.DataFrame(table) # Use raw table data
                    st.dataframe(df, width="stretch")
                    tables.append(df)
            else:
                st.write(f"No tables found on page {page_num}")

    return tables

def extract_tables_with_tabula(uploaded_file):
    """Extract tables using tabula-py library"""
    st.write("\n" + "=" * 50)
    st.write("EXTRACTING TABLES WITH TABULA")
    st.write("=" * 50)
    
    try:
        # Try to extract all tables from all pages
        tables = tabula.read_pdf(uploaded_file, pages='all', multiple_tables=True)
        
        if tables:
            st.write(f"Found {len(tables)} table(s) with tabula")
            for i, df in enumerate(tables):
                st.write(f"\nTable {i+1}:")
                st.dataframe(df, width="stretch")
        else:
            st.write("No tables found with tabula")
            
        return tables
    except Exception as e:
        st.write(f"Error with tabula: {e}")
        return []

def extract_tables_with_camelot(uploaded_file):
    """Extract tables using camelot library"""
    st.write("\n" + "=" * 50)
    st.write("EXTRACTING TABLES WITH CAMELOT")
    st.write("=" * 50)
    
    try:
        # Try lattice method first (for tables with clear borders)
        tables_lattice = camelot.read_pdf(uploaded_file, flavor='lattice', pages='all')
        
        if len(tables_lattice) > 0:
            st.write(f"Found {len(tables_lattice)} table(s) with camelot (lattice)")
            for i, table in enumerate(tables_lattice):
                st.write(f"\nTable {i+1} (lattice):")
                st.dataframe(table.df, width="stretch")
        
        # Try stream method (for tables without clear borders)
        tables_stream = camelot.read_pdf(uploaded_file, flavor='stream', pages='all')
        
        if len(tables_stream) > 0:
            st.write(f"Found {len(tables_stream)} table(s) with camelot (stream)")
            for i, table in enumerate(tables_stream):
                st.write(f"\nTable {i+1} (stream):")
                st.dataframe(table.df, width="stretch")
        
        return list(tables_lattice.tables + tables_stream.tables)
        
    except Exception as e:
        st.write(f"Error with camelot: {e}")
        return []

def extract_text_content(uploaded_file):
    """Extract all text content from PDF"""
    st.write("\n" + "=" * 50)
    st.write("EXTRACTING TEXT CONTENT")
    st.write("=" * 50)
    
    try:
        reader = PdfReader(uploaded_file)
        full_text = ""
        
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text:
                st.write(f"\nPage {page_num} text:")
                st.write(text)
                full_text += f"\n--- Page {page_num} ---\n{text}"
        
        return full_text
    except Exception as e:
        st.write(f"Error extracting text: {e}")
        return ""

def save_tables_to_csv(tables, method_name):
    """Save extracted tables to CSV files"""
    if not tables:
        st.write(f"No tables to save for {method_name}")
        return
    
    for i, table in enumerate(tables):
        if hasattr(table, 'df'):  # Camelot table object
            df = table.df
        else:  # Already a DataFrame
            df = table
            
        filename = f"table_{method_name}_{i+1}.csv"
        df.to_csv(filename, index=False)
        st.write(f"Saved table to {filename}")
    
    
# Extract tables using different methods
if uploaded_file is not None:
    pdfplumber_tables = extract_tables_with_pdfplumber(uploaded_file)
    tabula_tables = extract_tables_with_tabula(uploaded_file)
    camelot_tables = extract_tables_with_camelot(uploaded_file)
    
    # Extract text content
    text_content = extract_text_content(uploaded_file)
    
    # # Save tables to CSV files
    # save_tables_to_csv(pdfplumber_tables, "pdfplumber")
    # save_tables_to_csv(tabula_tables, "tabula")
    # save_tables_to_csv(camelot_tables, "camelot")
    
    # Save text content to file
    # if text_content:
    #     with open("extracted_text.txt", "w", encoding="utf-8") as f:
    #         f.write(text_content)
    #     st.write("Saved text content to extracted_text.txt")
    
    st.write("\n" + "=" * 50)
    st.write("EXTRACTION COMPLETE")
    st.write("=" * 50)
    st.write(f"PDFPlumber found: {len(pdfplumber_tables)} tables")
    st.write(f"Tabula found: {len(tabula_tables)} tables")
    st.write(f"Camelot found: {len(camelot_tables)} tables")
