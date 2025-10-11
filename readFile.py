import pdfplumber
import pandas as pd
import tabula
import camelot
from PyPDF2 import PdfReader
import os

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
                    df = pd.DataFrame(table[1:], columns=table[0] if table else None)
                    print(df.to_string())
                    tables.append(df)
            else:
                print(f"No tables found on page {page_num}")

    return tables

def extract_tables_with_tabula(pdf_path):
    """Extract tables using tabula-py library"""
    print("\n" + "=" * 50)
    print("EXTRACTING TABLES WITH TABULA")
    print("=" * 50)
    
    try:
        # Try to extract all tables from all pages
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        
        if tables:
            print(f"Found {len(tables)} table(s) with tabula")
            for i, df in enumerate(tables):
                print(f"\nTable {i+1}:")
                print(df.to_string())
        else:
            print("No tables found with tabula")
            
        return tables
    except Exception as e:
        print(f"Error with tabula: {e}")
        return []

def extract_tables_with_camelot(pdf_path):
    """Extract tables using camelot library"""
    print("\n" + "=" * 50)
    print("EXTRACTING TABLES WITH CAMELOT")
    print("=" * 50)
    
    try:
        # Try lattice method first (for tables with clear borders)
        tables_lattice = camelot.read_pdf(pdf_path, flavor='lattice', pages='all')
        
        if len(tables_lattice) > 0:
            print(f"Found {len(tables_lattice)} table(s) with camelot (lattice)")
            for i, table in enumerate(tables_lattice):
                print(f"\nTable {i+1} (lattice):")
                print(table.df.to_string())
        
        # Try stream method (for tables without clear borders)
        tables_stream = camelot.read_pdf(pdf_path, flavor='stream', pages='all')
        
        if len(tables_stream) > 0:
            print(f"Found {len(tables_stream)} table(s) with camelot (stream)")
            for i, table in enumerate(tables_stream):
                print(f"\nTable {i+1} (stream):")
                print(table.df.to_string())
        
        return tables_lattice.tables + tables_stream.tables
        
    except Exception as e:
        print(f"Error with camelot: {e}")
        return []

def extract_text_content(pdf_path):
    """Extract all text content from PDF"""
    print("\n" + "=" * 50)
    print("EXTRACTING TEXT CONTENT")
    print("=" * 50)
    
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text:
                print(f"\nPage {page_num} text:")
                print(text)
                full_text += f"\n--- Page {page_num} ---\n{text}"
        
        return full_text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def save_tables_to_csv(tables, method_name):
    """Save extracted tables to CSV files"""
    if not tables:
        print(f"No tables to save for {method_name}")
        return
    
    for i, table in enumerate(tables):
        if hasattr(table, 'df'):  # Camelot table object
            df = table.df
        else:  # Already a DataFrame
            df = table
            
        filename = f"table_{method_name}_{i+1}.csv"
        df.to_csv(filename, index=False)
        print(f"Saved table to {filename}")

def main():
    pdf_path = "Invoice_1479909_e209944.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found!")
        return
    
    print(f"Processing PDF: {pdf_path}")
    
    # Extract tables using different methods
    pdfplumber_tables = extract_tables_with_pdfplumber(pdf_path)
    tabula_tables = extract_tables_with_tabula(pdf_path)
    camelot_tables = extract_tables_with_camelot(pdf_path)
    
    # Extract text content
    text_content = extract_text_content(pdf_path)
    
    # Save tables to CSV files
    save_tables_to_csv(pdfplumber_tables, "pdfplumber")
    save_tables_to_csv(tabula_tables, "tabula")
    save_tables_to_csv(camelot_tables, "camelot")
    
    # Save text content to file
    if text_content:
        with open("extracted_text.txt", "w", encoding="utf-8") as f:
            f.write(text_content)
        print("Saved text content to extracted_text.txt")
    
    print("\n" + "=" * 50)
    print("EXTRACTION COMPLETE")
    print("=" * 50)
    print(f"PDFPlumber found: {len(pdfplumber_tables)} tables")
    print(f"Tabula found: {len(tabula_tables)} tables")
    print(f"Camelot found: {len(camelot_tables)} tables")

if __name__ == "__main__":
    main()
