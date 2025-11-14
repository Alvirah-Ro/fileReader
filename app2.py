""" 
Automated PDF table extractor: Version K
"""

import streamlit as st
import pdfplumber
import pandas as pd
# Import custom functions
from table_functions import (save_action_state, fix_concatenated_table, undo_fix_concatenated_action,
                             clean_duplicate_headers, undo_headers_action, update_display_table,
                             remove_duplicate_headers, undo_remove_duplicates_action, delete_unwanted_rows,
                             undo_delete_rows_action)

st.title('Automated PDF Table Extractor: Version K')

# File uploader for PDF invoice
uploaded_file = st.file_uploader("Upload a PDF invoice", type="pdf")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        all_tables = []

        # DEBUG: page_text = pdf.pages[0].extract_text()
        # DEBUG: st.text_area("Raw text (first 1000 chars):", page_text[:1000])
        with st.expander("View Raw Data or Original Tables"):
            for page_num, page in enumerate(pdf.pages, 1): # Start page numbering at 1
                tables = page.extract_tables()
                st.write(f"Found {len(tables)} table(s) on page {page_num}")
                if tables:
                    for i, table in enumerate(tables):
                        # DEBUG: st.write(f"DEBUG: Page {page_num}, Table {i + 1}")
                        col_raw, col_original = st.columns([1, 1])
                        with col_raw:
                            if st.button(f"Raw Data: Table {i + 1}, Page {page_num}", 
                                        key=f"show_raw_data_{page_num}_{i}", type="primary"):
                                st.write(f"#### Original Table {i + 1} from Page {page_num}:")
                                st.write(f"Raw: {table}")
                        df = pd.DataFrame(table)
                        with col_original:
                            if st.button(f"Original Table {i + 1}, Page {page_num}",
                                        key=f"show_original_table_{page_num}_{i}", type="primary"):
                                st.write(f"#### Original Table {i + 1} from Page {page_num}:")
                                st.dataframe(df, width="stretch")
                        all_tables.append(df)
                else:
                    page_text = page.extract_text()
                    st.write(f"No tables detected.  Click to see raw text from {page_num}:")
                    if st.button(f"Raw Text, Page {page_num}",
                                key=f"show_text_{page_num}", type="primary"):
                        st.text_area("Extracted text:", page_text, height=400)

        # Combine all tables and initialize session state
        if all_tables and 'main_table' not in st.session_state:
            combined_table = pd.concat(all_tables, ignore_index=True)
            st.session_state.main_table = combined_table
            # Convert dataframe to list of lists for processing
            st.session_state.table_as_list = combined_table.values.tolist()
            # Always preserve 
            st.session_state.original_table_data = st.session_state.table_as_list.copy()
            st.session_state.working_data = st.session_state.table_as_list.copy()
            st.session_state.current_headers = None
            st.success("Main table initialized!")

        # Show current processing status
        if 'current_headers' in st.session_state and st.session_state.current_headers:
            with st.expander("View Current Headers"):
                st.write("**Current Headers:**", st.session_state.current_headers)

        # Display current main table
        if 'main_table' in st.session_state:
            st.write(f"### All Tables Combined:")
            st.write(f"#### Current Main Table:")
            st.write("Click on options below to format table")
            st.dataframe(st.session_state.main_table, width="stretch")

        # Initialize applied actions tracking
        if 'applied_actions' not in st.session_state:
            st.session_state.applied_actions = []

        # Create columns for table and actions panel
        col_choices, col_break, col_actions = st.columns([3, 1, 3])

        with col_actions:
            st.write("### Applied Actions")
            if st.session_state.applied_actions:
                for i, action in enumerate(reversed(st.session_state.applied_actions)):
                    with st.container():
                        st.write(f"**{len(st.session_state.applied_actions) - i}. {action['name']}**")
                        st.write(f"_Applied at: {action['timestamp']}_")

                    # Specific undo button for each action type
                    if action['type'] == 'fix_concatenated':
                        if st.button(f"↶ Undo Fix", key=f"undo_fix_{action['id']}", type="secondary"):
                            undo_fix_concatenated_action(action['id'])

                    elif action['type'] == 'apply_headers':
                        if st.button(f"↶ Undo Headers", key=f"undo_headers_{action['id']}", type="secondary"):
                            undo_headers_action(action['id'])
                    
                    elif action['type'] == 'remove_duplicates':
                        if st.button(f"↶ Undo Remove Duplicates", key=f"undo_duplicates_{action['id']}", type="secondary"):
                            undo_remove_duplicates_action(action['id'])

                    elif action['type'] == 'delete_unwanted_rows':
                        if st.button(f"↶ Undo Delete Unwanted Rows", key=f"undo_delete_{action['id']}", type="secondary"):
                            undo_delete_rows_action(action['id'])

            else:
                st.info("No actions applied yet")

        with col_break:
            st.write("")
            
        with col_choices:
            # Header and Data start selection
            st.write("### Formatting Choices")

            # Choose row that contains headers
            with st.expander("Choose Headers"):
                st.write("#### Choose Header Row")
                if 'table_as_list' in st.session_state:
                    header_row_input = st.number_input("Select the first row that includes headers",
                                                    min_value=0, 
                                                    max_value=len(st.session_state.table_as_list) - 1 if 'table_as_list' in st.session_state else 10,
                                                    value=0,
                                                    key="header_row_selector")
        
                    if st.button("Click to Apply Headers", key="choose_headers_btn", type="primary"):
                        # Save current state before applying changes
                        action_id = save_action_state('apply_headers', f"Headers from row {header_row_input}")
                        clean_headers = clean_duplicate_headers(header_row_input)

                        # Update main table
                        update_display_table(st.session_state.working_data)
                        st.success(f"Headers applied from row {header_row_input}!")

            # Choose row where actual data starts
            with st.expander("Choose Data Start"):
                if 'current_headers' in st.session_state and st.session_state.current_headers:
                    # Row input for data start
                    data_start_input = st.number_input("Select the first row that contains actual data",
                                                min_value=header_row_input + 1,
                                                max_value=len(st.session_state.table_as_list),
                                                value=header_row_input + 1,
                                                key="data_start_selector")
                    if st.button("Apply Data Start", key="data_start_btn", type="primary"):
                        action_id = save_action_state('apply_data_start', f"Data starts at row {data_start_input}")

                        sliced_data = apply_data_start(data_start_input)

                         # Update main table
                        update_display_table(st.session_state.working_data)
                        st.success(f"Data now starts at former row {data_start_input}!")

            # Remove duplicate header rows
            with st.expander("Remove Duplicate Headers"):
                if 'header_row_index' in st.session_state and st.session_state.header_row_index is not None:
                    st.write(f"Will remove rows that match header row {st.session_state.header_row_index}")
                    if st.button("Remove Duplicate Header Hows", key = "remove_duplicates_btn", type="primary"):
                        # Save current state before applying changes
                        action_id = save_action_state('remove_duplicates', f"Remove Duplicate Headers (Row {st.session_state.header_row_index})")

                        # Work from current working data
                        source_data = st.session_state.working_data
                        cleaned_data = remove_duplicate_headers(source_data, st.session_state.header_row_index)

                        # Use helper function to handle formatting
                        update_display_table(cleaned_data)
                        st.success("Removed duplicate headers rows!")
                else:
                    st.info("Please select headers first to identify which rows to remove")

            # Fix concatenated data
            with st.expander("Fix Rows"):
                if st.button("Fix rows that have been combined", key="fix_concat_btn", type="primary"):
                    # Save current state before applying changes
                    action_id = save_action_state('fix_concatenated', "Fix Concatenated Rows")

                    # Always work from working data
                    source_data = st.session_state.working_data
                    fixed_table = fix_concatenated_table(source_data)
                    if fixed_table:
                        # Use helper function to handle all formatting automatically
                        update_display_table(fixed_table)
                        st.success("Table rows have been separated!")

            # Delete unwanted rows without real data
            with st.expander("Delete Rows"):
                # Input for choosing rows to delete
                delete_row_input = st.radio("Select which rows to remove - Column 1 should not include these values:",
                            ["empty space", "letters", "numbers", "symbols", "other"],
                            index=None,)
                
                # Show text input if "other" is selected
                custom_pattern = None
                if delete_row_input == "other":
                    custom_pattern = st.text_input("Enter custom regex pattern or text to search for:",
                                                   placeholder="e.g. Total|Subtotal or ^Page \\d+",
                                                   help="Use regex paterns or plain text. Examples: 'Total' (exact match), '^\\d{6}$' (6 digit numbers)")
                                                
                if st.button("Delete unwanted rows", key="del_rows_btn", type="primary"):
                    if delete_row_input is None:
                        st.error("Please select a row type to delete first")
                    elif delete_row_input == "other" and (not custom_pattern or custom_pattern.strip() == ""):
                        st.error("Please enter a custom pattern when 'other' is selected")
                    else:
                        # Save current state before applying changes
                        action_id = save_action_state('delete_unwanted_rows', "Delete Unwanted Rows")
                        
                        # Convert radio selection to regex pattern
                        if delete_row_input == "empty space":
                            search_pattern = r"^\s*$"  # Match empty or whitespace-only cells
                        elif delete_row_input == "letters":
                            search_pattern = r"^[A-Za-z\s]+$"  # Match cells with only letters and spaces
                        elif delete_row_input == "numbers":
                            search_pattern = r"^[\d\s.,]+$"  # Match cells with only numbers, spaces, commas, periods
                        elif delete_row_input == "symbols":
                            search_pattern = r"^[^\w\s]+$"  # Match cells with only symbols (no letters or numbers)
                        elif delete_row_input == "other":
                            search_pattern = custom_pattern # Use the custom pattern
                        
                        # Only proceed if we have a valid pattern
                        if search_pattern:
                            # Always work from working data
                            cleaned_table = delete_unwanted_rows(search_pattern)

                            if cleaned_table:
                                # Use helper function to handle all formatting automatically
                                update_display_table(cleaned_table)
                                st.success(f"Deleted rows where first cell contains: {delete_row_input}")
                                if 'debug_matches' in st.session_state:
                                    st.write("Rows that matched pattern:", st.session_state.debug_matches)
                                    del st.session_state.debug_matches

            # Reset button to start over
            if st.button("Reset to Original", key="reset_btn", type="primary"):
                if all_tables:
                    combined_table = pd.concat(all_tables, ignore_index=True)
                    st.session_state.main_table = combined_table
                    st.session_state.table_as_list = combined_table.values.tolist()
                    st.session_state.working_data = combined_table.values.tolist()

                    # Clear ALL session state variables including applied_actions
                    for key in ['current_headers', 'raw_headers', 'header_row_index', 'applied_actions']:
                        if key in st.session_state:
                            del st.session_state[key]

                    st.success("Table reset to original!")

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
