""" 
More simple automated PDF table extractor
"""

import streamlit as st
import pdfplumber
import pandas as pd
import re

st.title('Automated PDF Table Extractor')

# File uploader for PDF invoice
uploaded_file = st.file_uploader("Upload a PDF invoice", type="pdf")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        all_tables = []

        page_text = pdf.pages[0].extract_text()
        st.text_area("Raw text (first 1000 chars):", page_text[:1000])

        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) > 1: # Skip empty or single-row tables
                        df = pd.DataFrame(table)
                        all_tables.append(df)

        if all_tables:
            st.success(f"Found {len(all_tables)} table(s)")

            if len(all_tables) >= 3:
                table_3 = all_tables[2]

                # st.write("Table 3 shape:", table_3.shape)
                # st.write("Table 3 columns:", table_3.columns.tolist())
                # st.write("First few cells:")
                # st.write("Row 0, Col 0:", table_3.iloc[0, 0], type(table_3.iloc[0, 0]))
                # st.write("Row 1, Col 0:", table_3.iloc[1, 0], type(table_3.iloc[1, 0]))
                # st.write("Column name 0:", table_3.columns[0], type(table_3.columns[0]))

                header_text = table_3.iloc[0, 0]
                header_parts = re.split(r'\s+(?!#)', header_text)
                # Remove columns for Location (not needed) and BO (often empty)
                if "Location" in header_parts:
                    header_parts.remove("Location")
                if "BO" in header_parts:
                    header_parts.remove("BO")
                # temp_split = header_text.split()
                # header_parts = [f"{temp_split[0]} {temp_split[1]}"] + temp_split[2:]
                st.write("Original header:", header_text)
                st.write("Split header parts:", header_parts)

                cleaned_rows = []

                # Try to split data by patterns using numbers as column boundaries
                for idx, row in table_3.iterrows():
                    if idx > 0:
                        row_data = str(row.iloc[0]).strip()
                            # Split on newlines and take the last part (the current line)
                        if '\n' in row_data:
                            row_data = row_data.split('\n')[-1] # Take the last line
                        # st.write("Original row data:", row_data)
                        # Separating the Edition number in the first column from the rest of the data
                        parts = row_data.split(' ', 1)
                        st.write("Splitting the row data in 2 parts:", parts)
                        
                        # The rest of the data without the Edition number
                        remaining_data = parts[1]
                        # Right Split by spaces up to 6 splits (split from end of data to maintain title info stays together)
                        remaining_parts = remaining_data.rsplit(' ', 6)
                        remaining_parts = [p.strip() for p in remaining_parts if p.strip()]
                        st.write("Row Data starting with title info:", remaining_parts)
                        st.write(f"Remaining Parts repr: {repr(remaining_parts)}")

                        # Fix Backordered items that won't have data in all the columns
                        st.write("Last 2 columns:", remaining_parts[-2], remaining_parts[-1])
                        if (len(remaining_parts) >= 2 and
                            # Check if last item and second-to-last item are not prices
                            not re.match(r'^\d{1,3}\.\d{2}', remaining_parts[-1]) and
                            not re.match(r'^\d{1,3}\.\d{2}', remaining_parts[-2])):
                            special_parts = remaining_parts.copy()
                            st.write("Here is a copy of the BO item parts:", special_parts)
                            joined_special_parts = ' '.join(special_parts)
                            st.write("Rejoining parts:", joined_special_parts)
                            
                            # Split title from number ordered by number pattern
                            split_result = re.split(r'\s(\d{1,3})\s', joined_special_parts, 1)

                            if len(split_result) >= 3:
                                # First part is the title, second part is the number ordered, don't keep anything else
                                title = split_result[0].strip()
                                order_number = split_result[1].strip()

                                bo_parts = [title, order_number]
                                st.write("Reduced parts for BO:", bo_parts)

                                # Add message that item is on BO
                                bo_parts.append("Backordered Item")
                                st.write("Reduced parts for BO with BO label:", bo_parts)
                                # Reassign to remaining_parts
                                remaining_parts = bo_parts
                            else:
                                st.write("Could not split on number pattern")

                        else:
                            final_parts = remaining_parts.copy()
                                                    
                        st.write("First part:", parts[0])
                        # Put Edition # part and all other split parts back together
                        remaining_parts.insert(0, parts[0])
                        st.write("Final Parts put back together:", remaining_parts)

                        if len(remaining_parts) >= 3:
                            cleaned_rows.append(remaining_parts)
                
                if cleaned_rows:
                    max_cols = len(header_parts)

                    # Pad or trim each row to match header count
                    padded_rows = []
                    for row in cleaned_rows:
                        if len(row) < max_cols:
                            # Pad with empty strings
                            padded_row = row + [''] * (max_cols - len(row))
                        else:
                            # Trim to fit
                            padded_row = row[:max_cols]
                        padded_rows.append(padded_row)

                clean_table = pd.DataFrame(padded_rows, columns=header_parts)
                
                # Debug
                st.write("Debug - Title column data:")
                for i, title in enumerate(clean_table['Title'].head(3)):
                    st.write(f"Row {i}: '{title}' (type: {type(title)})")
                    st.write(f"Row {i} repr: {repr(title)}")

                # Apply cleaning to the Title column
                clean_table ['Title'] = clean_table['Title'].astype(str).str.replace(r'^[A-Z]\xad[A-Z0-9]+\xad[A-Z0-9]', '', regex=True)
                clean_table ['Title'] = clean_table['Title'].astype(str).str.replace(r'^/[A-Z0-9]+\xad[A-Z0-9]+', '', regex=True)

                st.write("### Cleaned Table 3:")
                st.dataframe(clean_table, width="stretch")




            for i, df in enumerate(all_tables, 1):
                st.write(f"### Table {i}")
                st.write(f"Size: {df.shape[0]} rows x {df.shape[1]} columns")
                st.dataframe(df, width="stretch")

                # Download button for each table
                csv = df.to_csv(index=False)
                st.download_button(
                    f"Download Table {i} as CSV",
                    csv,
                    f"table_{i}.csv",
                    key=f"download_{i}"
                )

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
