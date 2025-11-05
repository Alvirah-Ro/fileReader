""" 
Automated PDF table extractor: Version G
"""

import streamlit as st
import pdfplumber
import pandas as pd
import re

st.title('Automated PDF Table Extractor: Version G')

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
            st.success(f"Found {len(all_tables)} table(s)")
            
            # Get main tables from each page
            main_tables = []
            indices = [2, 6, 10, 14, 18]
            for i in indices:
                if i < len(all_tables) and i != (len(all_tables) - 1): # The last page might not include a main table
                    main_tables.append(all_tables[i])

            st.write("How many main tables we found:", len(main_tables))
                
            # Create a list for all the cleaned main tables
            clean_tables_list = []
            for table_index, table in enumerate(main_tables):
                # DEBUG: st.write(f"Processing table {table_index}")
                # Get the headers from the first main table
                if table_index == 0:
                    header_text = table.iloc[0, 0]
                    header_parts = re.split(r'\s+(?!#)', header_text)
                    # Remove columns for Location (not needed)
                    if "Location" in header_parts:
                        header_parts.remove("Location")

                    # Drop the first row from the first table after extracting header info
                    table = table.iloc[1:]

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
                        # DEBUG: st.write("Original row data:", row_data)
                        # Separating the Edition number in the first column from the rest of the data
                        parts = row_data.split(' ', 1)
                        # DEBUG: st.write("Splitting the row data in 2 parts:", parts)
                        
                        # The rest of the data without the Edition number
                        remaining_data = parts[1]
                        # Right Split by spaces up to 4 splits (split from end of data to maintain title info stays together)
                        # 4 splits stops before the BO column
                        remaining_parts = remaining_data.rsplit(' ', 4)
                        remaining_parts = [p.strip() for p in remaining_parts if p.strip()]
                        # DEBUG st.write("Row Data after splitting the last 4 columns", remaining_parts)
                        # DEBUG st.write("Row Data after splitting the last 4 columns", remaining_parts)
                        # DEBUG st.write(f"Remaining Parts repr: {repr(remaining_parts)}")

                        # Get the first item (title + all numbers)
                        title_and_numbers = remaining_parts[0]
                        # DEBUG st.write("title_and_numbers:", title_and_numbers)
                        # DEBUG st.write("Everything else:", remaining_parts[1:])

                        # Right split to try and find 3 numbers in case of partial orders
                        number_parts = title_and_numbers.rsplit(' ', 3)
                        # DEBUG st.write("Row data after trying to split off 3 numbers from the end of the title:", number_parts)
                        # If there are not 3 numbers, the second part will not be a number, it will be part of the title
                        
                        # DEBUG - checking for title information in wrong parts
                        # DEBUG if not number_parts[1].isdigit():
                            # DEBUG st.write("This is not a number in index 1:", number_parts[1])
                        # DEBUG if not number_parts[2].isdigit():
                            # DEBUG st.write("This is not a number in index 2:", number_parts[2])

                        # If neither are a number, then it is all title information
                        if (not number_parts[1].isdigit() and not number_parts[2].isdigit()):
                            title_part = [" ".join(number_parts[:3])]
                            final_number_parts = [number_parts[3]]
                            # DEBUG st.write("Rejoined title part if there were no numbers:", title_part)
                            # DEBUG st.write("The remaining parts are:", final_number_parts)
                            final_parts = title_part + final_number_parts + remaining_parts[1:]
                            # DEBUG st.write("Final parts put together:", final_parts)
                            # Check if there is still title information lingering in the order column
                            if not final_parts[1].isdigit():
                                # DEBUG st.write("This is not a number in index 1:", final_parts[1])
                                new_title_part = [" ".join(final_parts[:2])]
                                # DEBUG st.write("New rejoined title part:", new_title_part)
                                final_parts = new_title_part + remaining_parts[2:]
                                # DEBUG st.write("Final parts again:", final_parts)

                            if (len(final_parts) >= 2 and
                                # Check if last item and second-to-last item are not prices
                                # If they are not prices, then the item is on backorder
                                (not re.match(r'^\d{1,3}\.\d{2}', final_parts[-1]) or
                                not re.match(r'^\d{1,3}\.\d{2}', final_parts[-2]))):
                                # DEBUG st.write("This is a backordered item: remaining_parts for BOs:", final_parts)
                                # Insert a shipped column because the second number is the amount backordered
                                final_parts.insert(2, " ")
                                # DEBUG st.write("After inserting an empty column for shipped quantity:", final_parts)

                                # Insert another column if there is not a list price
                                if re.search(r'%', final_parts[4]):
                                    # DEBUG st.write("There is a precentage in index 4 for this item:", final_parts[4])
                                    # Insert another column if there is not a list price
                                    final_parts.insert(4, " ")
                                    # DEBUG st.write("Adding another column because there was no list price", final_parts)
                                # Reassign to remaining_parts
                                remaining_parts = final_parts
                                # DEBUG st.write("This should be our final data for any backordered items:", final_parts)

                        elif not number_parts[1].isdigit():
                            title_part = [" ".join(number_parts[:2])]
                            # DEBUG st.write("Rejoined title part if there were only 2 numbers:", title_part)
                            final_number_parts = number_parts[-2:]
                            # Add an empty string to go in the BO column if all were shipped and none were backordered
                            final_number_parts.append(" ")
                            # DEBUG st.write("The final number parts after adding a BO column are:", final_number_parts)

                            # Check if the final_number_parts are all numbers
                            # DEBUG if not final_number_parts[0].isdigit():
                                # DEBUG st.write("The first final number is not a number:", final_number_parts[0])

                            # Add title to new number parts to remaining columns
                            remaining_parts = title_part + final_number_parts + remaining_parts[1:]
                            # DEBUG st.write("After adding everything back together:", remaining_parts)

                            # Check if there is a number in the Order Column or if it is still title information
                            if not remaining_parts[1].isdigit():
                                # DEBUG st.write("This is not a number in the order column:", remaining_parts[1])
                                more_title_part = [" ".join(remaining_parts[:2])]
                                # DEBUG st.write("Rejoined title part:", more_title_part)
                                remaining_parts = more_title_part + remaining_parts[2:]
                                # DEBUG st.write("Trying to put back together again with fixed title:", remaining_parts)

                            

                        else:
                            # DEBUG st.write(f"* There are 3 numbers so this could be a partial backorder for item {number_parts[0]}")

                            # No need to do anything else, title is already separate from 3 numbers
                            # Add number_parts (which includes a title part) to remaining columns
                            remaining_parts = number_parts + remaining_parts[1:]
                            # DEBUG st.write("After adding everything back together for partial backordered items:", remaining_parts)
                            # If it is a partial backorder, Order quantity should equal Ship quantity + BO quantity
                            # DEBUG if int(remaining_parts[1]) == int(remaining_parts[2]) + int(remaining_parts[3]):
                                # DEBUG st.write("Math!  The numbers add up for a partial backorder")
                                # DEBUG st.write(f"{remaining_parts[1]} equals {remaining_parts[2]} plus {remaining_parts[3]}")
                            # DEBUG else:
                                # DEBUG st.write(f"{remaining_parts[1]} does not equal {remaining_parts[2]} plus {remaining_parts[3]}")
                                # DEBUG st.write("The math doesn't work so it is probably not a partial backorder")

                            # DEBUG: Check if the title ends in the word vol (case insensitive)
                            # DEBUG if re.search(r'vol', number_parts[0], re.I):
                                # DEBUG st.write("The word 'vol' is in this title", number_parts[0])

                            # Now fix the title if it is not a partial backorder:    
                            if not int(remaining_parts[1]) == int(remaining_parts[2]) + int(remaining_parts[3]):
                                # DEBUG st.write("This title needs to be fixed:", number_parts[0])
                                title_part = [" ".join(number_parts[:2])]
                                # DEBUG st.write("Correcting the title part:", title_part)
                                # DEBUG st.write("Remaining_parts:", remaining_parts[2:])
                                remaining_parts = title_part + remaining_parts[2:]
                                # Add the empty backorder column
                                remaining_parts.insert(3, " ")
                                # DEBUG st.write("Final Data with corrected title:", remaining_parts)

                        # DEBUG: st.write("First part:", parts[0])
                        # Put Edition # part and all other split parts back together
                        remaining_parts.insert(0, parts[0])
                        # DEBUG: st.write("Final Parts put back together after inserting parts[0]:", remaining_parts)
                        # DEBUG: st.write("Length check - len(remaining_parts) >=3?", len(remaining_parts) >= 3)

                        if len(remaining_parts) >= 3:
                            # DEBUG: st.write("Before appending: cleaned_rows has:", len(cleaned_rows), "items")
                            # DEBUG: st.write("Adding this row:", remaining_parts)
                            cleaned_rows.append(remaining_parts)
                            # DEBUG: st.write("After appending: cleaned_rows now has", len(cleaned_rows), "items")
                            # DEBUG: st.write("Last item in cleaned_rows:", cleaned_rows[-1])
                        # DEBUG else:
                            # DEBUG st.write("Not adding - remaining_parts too short:", remaining_parts, "Length:", len(remaining_parts))
                        
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
                    # DEBUG: st.write("Final Padded Rows:", padded_rows)

                    clean_table = pd.DataFrame(padded_rows, columns=header_parts)
                    # Add cleaned table to list of all cleaned tables
                    clean_tables_list.append(clean_table)

                    # Apply cleaning to the Title column to remove unwanted location data
                    # DEBUG st.write("Title info before any cleaning of location data repr:", clean_table['Title'])
                    # Create a mask - a boolean filter to identify which rows meet this condition
                    mask1 = clean_table['Title'].str.match(r'^[A-Z]\xad[A-Z0-9]+', na=False)
                    clean_table.loc[mask1, 'Title'] = clean_table.loc[mask1, 'Title'].str.split(' ', n=1).str[1] # Split at first space & take everything else
                    # DEBUG st.write("After first effort to clean up title info:", clean_table['Title'])
                    # Create a new mask to keep filtering out lingering location data from the title data
                    mask2 = clean_table['Title'].str.match(r'^\xad[A-Z0-9]+', na=False)
                    clean_table.loc[mask2, 'Title'] = clean_table.loc[mask2, 'Title'].str.split(' ', n=1).str[1]
                    # DEBUG st.write("After second effort to clean up title info:", clean_table['Title'])

                    # Create a third mask to keep filtering out lingering location data from the title data
                    mask3 = clean_table['Title'].str.match(r'^/', na=False)
                    clean_table.loc[mask3, 'Title'] = clean_table.loc[mask3, 'Title'].str.split(' ', n=2).str[2]
                    # DEBUG st.write("After third effort to clean up title info:", clean_table['Title'])

                    # Create a fourth mask to keep filtering out lingering location data from the title data
                    mask4 = clean_table['Title'].str.match(r'^[0-9][0-9]', na=False)
                    clean_table.loc[mask4, 'Title'] = clean_table.loc[mask4, 'Title'].str.split(' ', n=1).str[1]
                    # DEBUG st.write("After third effort to clean up title info:", clean_table['Title'])

                st.write(f"### Cleaned Main Table", table_index)
                st.dataframe(clean_table, width="stretch")

            if clean_tables_list:
                combined_clean_table = pd.concat(clean_tables_list, ignore_index=True)
                # Force Edition column to be treated as text in Excel
                combined_clean_table['Edition #'] = '"' + combined_clean_table['Edition #'].astype(str) + '"'

                st.write("### All Main Tables Combined:")
                st.dataframe(combined_clean_table, width="stretch")

                
                # Debug
                # st.write("Debug - Title column data:")
                # for i, title in enumerate(clean_table['Title'].head(3)):
                    # st.write(f"Row {i}: '{title}' (type: {type(title)})")
                    # st.write(f"Row {i} repr: {repr(title)}")

            # DEBUG: Show all tables found
            # for i, df in enumerate(all_tables, 1):
            #     st.write(f"### Table {i}")
            #     st.write(f"Size: {df.shape[0]} rows x {df.shape[1]} columns")
            #     st.dataframe(df, width="stretch")

                # # Download button for each table
                # csv = df.to_csv(index=False)
                # st.download_button(
                #     f"Download Table {i} as CSV",
                #     csv,
                #     f"table_{i}.csv",
                #     key=f"download_{i}"
                # )

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
