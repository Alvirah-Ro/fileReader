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

        # Debugging
        # page_text = pdf.pages[0].extract_text()
        # st.text_area("Raw text (first 1000 chars):", page_text[:1000])

        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) > 1: # Skip empty or single-row tables
                        df = pd.DataFrame(table)
                        all_tables.append(df)

        if all_tables:
            st.success(f"Found {len(all_tables)} table(s)")
            
            # Get main tables from each page
            main_tables = []
            indices = [2, 6, 10, 14, 18]
            for i in indices:
                if i < len(all_tables) and i != (len(all_tables) - 1): # The last page might not include a main table
                    main_tables.append(all_tables[i])

            st.write("How many main tables we found:", len(main_tables))
                
                #table_3 = all_tables[2]

                # st.write("Table 3 shape:", table_3.shape)
                # st.write("Table 3 columns:", table_3.columns.tolist())
                # st.write("First few cells:")
                # st.write("Row 0, Col 0:", table_3.iloc[0, 0], type(table_3.iloc[0, 0]))
                # st.write("Row 1, Col 0:", table_3.iloc[1, 0], type(table_3.iloc[1, 0]))
                # st.write("Column name 0:", table_3.columns[0], type(table_3.columns[0]))
            
            # Create a list for all the cleaned main tables
            clean_tables_list = []
            for table_index, table in enumerate(main_tables):
                # st.write(f"Processing table {table_index}")
                # Get the headers from the first main table
                if table_index == 0:
                    header_text = table.iloc[0, 0]
                    header_parts = re.split(r'\s+(?!#)', header_text)
                    # Remove columns for Location (not needed)
                    if "Location" in header_parts:
                        header_parts.remove("Location")

                    # Drop the first row from the first table after extracting header info
                    table = table.iloc[1:]

                    # temp_split = header_text.split()
                    # header_parts = [f"{temp_split[0]} {temp_split[1]}"] + temp_split[2:]
                    # st.write("Original header:", header_text)
                    # st.write("Split header parts:", header_parts)

                cleaned_rows = []

                # Try to split data by patterns using numbers as column boundaries
                for idx, row in table.iterrows():
                    # This (if idx > 0) was originally to remove any duplicate headers,
                    # but the headers only need to be removed on the page 1 table,
                    # otherwise it was skipping rows of actual data so I canged it to >= 0
                    if idx >= 0:
                        row_data = str(row.iloc[0]).strip()
                            # Split on newlines and take the last part (the current line)
                            # Some of the Edition numbers were showing up in multiple rows without this code
                        if '\n' in row_data:
                            row_data = row_data.split('\n')[-1] # Take the last line
                        st.write("Original row data:", row_data)
                        # Separating the Edition number in the first column from the rest of the data
                        parts = row_data.split(' ', 1)
                        # st.write("Splitting the row data in 2 parts:", parts)
                        
                        # The rest of the data without the Edition number
                        remaining_data = parts[1]
                        # Right Split by spaces up to 4 splits (split from end of data to maintain title info stays together)
                        # 4 splits stops before the BO column
                        remaining_parts = remaining_data.rsplit(' ', 4)
                        remaining_parts = [p.strip() for p in remaining_parts if p.strip()]
                        st.write("Row Data after splitting the last 4 columns", remaining_parts)
                        # DEBUG st.write(f"Remaining Parts repr: {repr(remaining_parts)}")

                        # Get the first item (title + all numbers)
                        title_and_numbers = remaining_parts[0]
                        st.write("title_and_numbers:", title_and_numbers)
                        st.write("Everything else:", remaining_parts[1:])

                        # Right split to try and find 3 numbers in case of partial orders
                        number_parts = title_and_numbers.rsplit(' ', 3)
                        st.write("Row data after trying to split off 3 numbers from the end of the title:", number_parts)
                        # If there are not 3 numbers, the second part will not be a number, it will be part of the title
                        
                        # DEBUG - checking for title information in wrong parts
                        if not number_parts[1].isdigit():
                            st.write("This is not a number in index 1:", number_parts[1])
                        if not number_parts[2].isdigit():
                            st.write("This is not a number in index 2:", number_parts[2])

                        # If neither are a number, then it is all title information
                        if (not number_parts[1].isdigit() and not number_parts[2].isdigit()):
                            title_part = [" ".join(number_parts[:3])]
                            final_number_parts = [number_parts[3]]
                            st.write("Rejoined title part if there were no numbers:", title_part)
                            st.write("The remaining parts are:", final_number_parts)
                            final_parts = title_part + final_number_parts + remaining_parts[1:]
                            st.write("Final parts put together:", final_parts)
                            # Check if there is still title information lingering in the order column
                            if not final_parts[1].isdigit():
                                st.write("This is not a number in index 1:", final_parts[1])
                                new_title_part = [" ".join(final_parts[:2])]
                                st.write("New rejoined title part:", new_title_part)
                                final_parts = new_title_part + remaining_parts[2:]
                                st.write("Final parts again:", final_parts)

                            if (len(final_parts) >= 2 and
                                # Check if last item and second-to-last item are not prices
                                # If they are not prices, then the item is on backorder
                                (not re.match(r'^\d{1,3}\.\d{2}', final_parts[-1]) or
                                not re.match(r'^\d{1,3}\.\d{2}', final_parts[-2]))):
                                st.write("This is a backordered item: remaining_parts for BOs:", final_parts)
                                # Insert a shipped column because the second number is the amount backordered
                                final_parts.insert(2, " ")
                                st.write("After inserting an empty column for shipped quantity:", final_parts)

                                # Insert another column if there is not a list price
                                if re.search(r'%', final_parts[4]):
                                    st.write("There is a precentage in index 4 for this item:", final_parts[4])
                                    # Insert another column if there is not a list price
                                    final_parts.insert(4, " ")
                                    st.write("Adding another column because there was no list price", final_parts)
                                # Reassign to remaining_parts
                                remaining_parts = final_parts
                                st.write("This should be our final data for any backordered items:", final_parts)

                        elif not number_parts[1].isdigit():
                            title_part = [" ".join(number_parts[:2])]
                            st.write("Rejoined title part if there were only 2 numbers:", title_part)
                            final_number_parts = number_parts[-2:]
                            # Add an empty string to go in the BO column if all were shipped and none were backordered
                            final_number_parts.append(" ")
                            st.write("The final number parts after adding a BO column are:", final_number_parts)

                            # Check if the final_number_parts are all numbers
                            if not final_number_parts[0].isdigit():
                                st.write("The first final number is not a number:", final_number_parts[0])
                                # TO DO: move other backorder logic here to handle all BOs earlier

                            # Add title to new number parts to remaining columns
                            remaining_parts = title_part + final_number_parts + remaining_parts[1:]
                            st.write("After adding everything back together:", remaining_parts)

                            # Check if there is a number in the Order Column or if it is still title information
                            if not remaining_parts[1].isdigit():
                                st.write("This is not a number in the order column:", remaining_parts[1])
                                more_title_part = [" ".join(remaining_parts[:2])]
                                st.write("Rejoined title part:", more_title_part)
                                remaining_parts = more_title_part + remaining_parts[2:]
                                st.write("Trying to put back together again with fixed title:", remaining_parts)

                            

                        else:
                            st.write(f"* There are 3 numbers so this could be a partial backorder for item {number_parts[0]}")

                            # No need to do anything else, title is already separate from 3 numbers
                            # Add number_parts (which includes a title part) to remaining columns
                            remaining_parts = number_parts + remaining_parts[1:]
                            st.write("After adding everything back together for partial backordered items:", remaining_parts)
                            # If it is a partial backorder, Order quantity should equal Ship quantity + BO quantity
                            if int(remaining_parts[1]) == int(remaining_parts[2]) + int(remaining_parts[3]):
                                st.write("Math!  The numbers add up for a partial backorder")
                                st.write(f"{remaining_parts[1]} equals {remaining_parts[2]} plus {remaining_parts[3]}")
                            else:
                                st.write(f"{remaining_parts[1]} does not equal {remaining_parts[2]} plus {remaining_parts[3]}")
                                st.write("The math doesn't work so it is probably not a partial backorder")

                            # DEBUG: Check if the title ends in the word vol (case insensitive)
                            if re.search(r'vol', number_parts[0], re.I):
                                st.write("The word 'vol' is in this title", number_parts[0])

                            # Now fix the title if it is not a partial backorder:    
                            if re.search(r'vol', number_parts[0], re.I) or (not int(remaining_parts[1]) == int(remaining_parts[2]) + int(remaining_parts[3])):
                                st.write("This title needs to be fixed:", number_parts[0])
                                title_part = [" ".join(number_parts[:2])]
                                st.write("Correcting the title part:", title_part)
                                st.write("Remaining_parts:", remaining_parts[2:])
                                remaining_parts = title_part + remaining_parts[2:]
                                # Add the empty backorder column
                                remaining_parts.insert(3, " ")
                                st.write("Final Data with corrected title:", remaining_parts)

                        # st.write("First part:", parts[0])
                        # Put Edition # part and all other split parts back together
                        remaining_parts.insert(0, parts[0])
                        # st.write("Final Parts put back together after inserting parts[0]:", remaining_parts)
                        # st.write("Length check - len(remaining_parts) >=3?", len(remaining_parts) >= 3)

                        if len(remaining_parts) >= 3:
                            # st.write("Before appending: cleaned_rows has:", len(cleaned_rows), "items")
                            # st.write("Adding this row:", remaining_parts)
                            cleaned_rows.append(remaining_parts)
                            # st.write("After appending: cleaned_rows now has", len(cleaned_rows), "items")
                            # st.write("Last item in cleaned_rows:", cleaned_rows[-1])
                        else:
                            st.write("Not adding - remaining_parts too short:", remaining_parts, "Length:", len(remaining_parts))
                        
                if cleaned_rows:
                    # st.write("Creating Dataframe from cleaned_rows with", len(cleaned_rows), "items:")
                    # DEBUG for idx, row in enumerate(cleaned_rows):
                        # DEBUG st.write(f"Row {idx}: {row}")
                    max_cols = len(header_parts)

                    # Pad or trim each row to match header count
                    padded_rows = []
                    for row in cleaned_rows:
                        if len(row) < max_cols:
                            # Pad with empty strings
                            padded_row = row + [''] * (max_cols - len(row))
                            # st.write(f"After padding row {row} there are {len(padded_row)} columns")
                        else:
                            # Trim to fit
                            padded_row = row[:max_cols]
                        padded_rows.append(padded_row)
                    # st.write("Final Padded Rows:", padded_rows)

                    clean_table = pd.DataFrame(padded_rows, columns=header_parts)
                    # Add cleaned table to list of all cleaned tables
                    clean_tables_list.append(clean_table)

                    # Apply cleaning to the Title column to remove unwanted location data
                    st.write(f"Title info before any cleaning of location data repr: {repr(clean_table['Title'])}")
                    # Create a mask - a boolean filter to identify which rows meet this condition
                    mask = clean_table['Title'].str.match(r'^[A-Z]\xad[A-Z0-9]+\xad[A-Z0-9]', na=False)
                    clean_table.loc[mask, 'Title'] = clean_table.loc[mask, 'Title'].str.split(' ', n=1).str[1] # Split at first space & take everything else
                    st.write("trying to clean up title info:", clean_table['Title'])
                    # clean_table ['Title'] = clean_table['Title'].astype(str).str.replace(r'^[A-Z]\xad[A-Z0-9]+\xad[A-Z0-9]', '', regex=True)
                    # st.write(f"Title info after first cleaning repr: {repr(clean_table['Title'])}")
                    # clean_table ['Title'] = clean_table['Title'].astype(str).str.replace(r'^/[A-Z0-9]+\xad[A-Z0-9]+', '', regex=True)
                    # st.write(f"Title info after second cleaning repr: {repr(clean_table['Title'])}")


                st.write(f"### Cleaned Main Table", table_index)
                st.dataframe(clean_table, width="stretch")

            if clean_tables_list:
                combined_clean_table = pd.concat(clean_tables_list, ignore_index=True)
                # Force all columns to be treated as text in Excel (this is not currenlty working in Numbers)
                for col in combined_clean_table.columns:
                    combined_clean_table[col] = '"' + combined_clean_table[col].astype(str) + '"'

                st.write("### All Main Tables Combined:")
                st.dataframe(combined_clean_table, width="stretch")

                
                # Debug
                # st.write("Debug - Title column data:")
                # for i, title in enumerate(clean_table['Title'].head(3)):
                    # st.write(f"Row {i}: '{title}' (type: {type(title)})")
                    # st.write(f"Row {i} repr: {repr(title)}")

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
