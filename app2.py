""" 
Automated PDF table extractor: Version A
"""

import streamlit as st
import pdfplumber
import pandas as pd
# Import custom functions
from table_functions import (save_action_state, choose_headers, apply_data_start,
                             fix_concatenated_table, update_display_table, remove_duplicate_headers,
                             delete_unwanted_rows, add_net_item_col)

from undo_table_functions import (undo_choose_headers_action, undo_data_start_action,
                                  undo_delete_rows_action, undo_fix_concatenated_action,
                                  undo_net_item_col_action, undo_remove_duplicates_action)

from template_functions import (save_template_to_disk, build_template_from_actions,
                                list_templates, load_template_from_disk, replay_template,
                                action_label)

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
            st.session_state.original_table_data = [r[:] for r in st.session_state.table_as_list]
            st.session_state.working_data = [r[:] for r in st.session_state.table_as_list]
            st.session_state.current_headers = None
            st.success("Main table initialized!")

        # Show current processing status
        if 'current_headers' in st.session_state and st.session_state.current_headers:
            with st.expander("View Current Headers"):
                st.write("**Current Headers:**", st.session_state.current_headers)

        # Display current main table
        if 'main_table' in st.session_state:
            st.write(f"#### Current Main Table (all tables combined):")
            st.write("Click on options below to format table")
            st.dataframe(st.session_state.main_table, width="stretch")

        # Initialize applied actions tracking
        if 'applied_actions' not in st.session_state:
            st.session_state.applied_actions = []

        # Create columns for table and actions panel
        col_choices, col_break, col_actions = st.columns([4, 1, 2])

        # Column on the left to display formatting choices    
        with col_choices:
            # Header and Data start selection
            st.write("### Formatting Choices")



            tab1, tab2, tab3, tab4 = st.tabs(["Headers", "Rows", "Columns", "Templates"])

            with tab1:
                # Choose row that contains headers
                with st.expander("Choose Headers"):
                    with st.form("header_form"):
                        st.write("#### Choose Header Row")

                        if 'table_as_list' in st.session_state:
                            header_row_input = st.number_input("Select the first row that includes headers",
                                                            min_value=0,
                                                            max_value=len(st.session_state.table_as_list) - 1 if 'table_as_list' in st.session_state else 10,
                                                            value=0,
                                                            key="header_row_selector")

                            # Wrap in a form to keep expander open when changing inputs
                            if st.form_submit_button("Click to Apply Headers", key="choose_headers_btn", type="primary"):
                                # Save current state before applying changes
                                params={'header_row_index': int(header_row_input)}
                                name = action_label('apply_headers', params)
                                save_action_state('apply_headers', name, params=params)
                                
                                choose_headers(header_row_input)
                                st.session_state.header_row_index = int(header_row_input)
                                # Automatically start data after header row
                                st.session_state.data_start_index = st.session_state.header_row_index + 1

                                # Update main table
                                update_display_table(st.session_state.working_data)
                                st.toast(f"Headers applied from row {header_row_input}!")
                                st.rerun()

                            # Remove duplicate header rows
                with st.expander("Remove Duplicate Headers"):
                    if 'header_row_index' in st.session_state and st.session_state.header_row_index is not None:
                        st.write("Will remove rows that match header row")
                        if st.button("Remove Duplicate Header Rows", key = "remove_duplicates_btn", type="primary"):
                            # Save current state before applying changes
                            params={'header_row_index': int(st.session_state.get('header_row_index', 0))}
                            name = action_label('remove_duplicates', params)
                            save_action_state('remove_duplicates', name, params=params)

                            # Work from current working data
                            source_data = st.session_state.working_data
                            cleaned_data = remove_duplicate_headers(source_data, st.session_state.header_row_index)

                            # Use helper function to handle formatting
                            update_display_table(cleaned_data)
                            st.success("Removed duplicate header rows!")
                            st.rerun()
                    else:
                        st.info("Please select headers first to identify which rows to remove")



                # # Choose row where actual data starts
                # with st.expander("Choose Data Start"):
                #     if 'current_headers' in st.session_state and st.session_state.current_headers:
                #         # Row input for data start
                #         data_start_input = st.number_input("Select the first row that contains actual data",
                #                                     min_value=st.session_state.get('header_row_index', 0) + 1,
                #                                     max_value=len(st.session_state.working_data) - 1,
                #                                     value=st.session_state.get('header_row_index', 0) + 1,
                #                                     key="data_start_selector")
                        
                #         if st.button("Apply Data Start", key="data_start_btn", type="primary"):
                #                 params={'data_start_index': int(data_start_input)}
                #                 name = action_label('apply_data_start', params)
                #                 save_action_state('apply_data_start', name, params=params)

                #                 apply_data_start(data_start_input) # Set the index only

                #                 # Update main table
                #                 update_display_table(st.session_state.working_data)
                #                 st.success(f"Data now starts at former row {data_start_input}!")
                #                 st.rerun()

            with tab2:

                # Fix concatenated data
                with st.expander("Separate Rows"):
                    if st.button("Fix rows that have been combined", key="fix_concat_btn", type="primary"):
                        # Save current state before applying changes
                            params={}
                            name = action_label('fix_concatenated', params)
                            save_action_state('fix_concatenated', name, params=params)

                            # Always work from working data
                            source_data = st.session_state.working_data
                            fixed_table = fix_concatenated_table(source_data)
                            if fixed_table:
                                # Use helper function to handle all formatting automatically
                                update_display_table(fixed_table)
                                st.success("Table rows have been separated!")
                                st.rerun()

                # Delete unwanted rows without real data
                with st.expander("Delete Rows"):
                    # Input for choosing rows to delete
                    delete_row_input = st.radio("Select which rows to delete - First cells (Column 1) should not include these values:",
                                ["Empty", "Letters", "Numbers", "Symbols", "Other"],
                                index=None,)
                    
                    # Show text input if "other" is selected
                    search_pattern = None
                    custom_pattern = None
                    if delete_row_input == "other":
                        custom_pattern = st.text_input("Enter custom regex pattern or text to search for:",
                                                    placeholder="e.g. Total|Subtotal or ^\\d{6}$' or ^Page \\d+",
                                                    help="Use regex patterns or plain text. Examples: 'Total' (exact match), '^\\d{6}$' (6 digit numbers)")
                                                    
                    if st.button("Delete unwanted rows", key="del_rows_btn", type="primary"):
                        if delete_row_input is None:
                            st.error("Please select a row type to delete first")
                            st.stop() # Early exit to halt remainder of script for this rerun
                        if delete_row_input == "other" and (not custom_pattern or custom_pattern.strip() == ""):
                            st.error("Please enter a custom pattern when 'other' is selected")
                            st.stop()# Early exit to halt remainder of script for this rerun
                        
                        # Map choice to regex with a dictionary
                        mapping = {
                            "Empty": r"^\s*$",  # Match empty or whitespace-only cells
                            "Letters": r"^[A-Za-z\s]+$",  # Match cells with only letters and spaces
                            "Numbers": r"^[\d\s.,]+$",  # Match cells with only numbers, spaces, commas, periods
                            "Symbols": r"^[^\w\s]+$"  # Match cells with only symbols (no letters or numbers)
                        }
                        search_pattern = mapping.get(delete_row_input, custom_pattern
                                                    )
                        # Save current state before applying changes
                        params={                                
                            'pattern': search_pattern,
                            'choice': delete_row_input, # optional (e.g., 'letters', 'numbers', 'other')
                            'scope': 'first_cell'
                        }
                        name = action_label('delete_unwanted_rows', params)
                        save_action_state('delete_unwanted_rows', name, params=params)
                        
                        cleaned_table = delete_unwanted_rows(search_pattern)
                        if cleaned_table:
                            # Use helper function to handle all formatting automatically
                            update_display_table(cleaned_table)
                            if 'debug_matches' in st.session_state:
                                st.write("Rows that matched pattern:", st.session_state.debug_matches)
                                del st.session_state.debug_matches
                            st.success(f"Deleted rows where first cell contains: {delete_row_input if delete_row_input != 'other' else custom_pattern}")
                            st.rerun()
            with tab3:

                with st.expander("Alter columns"):
                    st.write("Add a Net-per-Item Column")
                    retail_price_input = st.number_input("Column number for retail price (1 = first column)",
                                                    min_value=1,
                                                    max_value=max((len(r) for r in st.session_state.working_data),
                                                                        default=0),
                                                    value=1,
                                                    key="retail_price_col_selector"
                                                    )
                    discount_percent_input = st.number_input("Column number for discount percent (1 = first column)",
                                                    min_value=1,
                                                    max_value=max((len(r) for r in st.session_state.working_data),
                                                                        default=0),
                                                    value=1,
                                                    key="discount_percent_col_selector"
                                                    )
                    
                    # Subtract 1 since users will be using 1 base instead of 0 base indexing
                    retail_idx = retail_price_input - 1
                    discount_idx = discount_percent_input - 1

                    if st.button("Add Net-per-Item Column", type="primary"):
                        params={
                            'retail_price_index' : int(retail_idx),
                            'discount_percent_index' : int(discount_idx)
                        }
                        name = action_label('add_net_item_col', params)
                        save_action_state('add_net_item_col', name, params=params)

                        added_net_table = add_net_item_col(retail_idx, discount_idx)       
                        update_display_table(added_net_table)
                        st.success("Added Net-per-Item Column")
                        st.rerun()

            with tab4:
                
                # Button to save template to disk
                if st.session_state.applied_actions:
                    st.write("#### Save Template")
                    template_name = st.text_input("Please enter name of template")
                    if template_name:
                        st.session_state.template_name = template_name
                        if st.button("Click to save template"):
                            tpl = build_template_from_actions(st.session_state.applied_actions)
                            for w in tpl.get("warnings", []):
                                st.warning(w)

                            path = save_template_to_disk(tpl)
                            st.success(f"Template: {template_name} saved!")


                st.write("#### Load Template")
                template_list = list_templates() # Returns list of filenames

                if not template_list:
                    st.info("No templates saved yet.")
                else:
                    selected = st.selectbox(
                        "Choose a template to apply",
                        template_list,
                        index=None,
                        placeholder="Select template"
                    )
                    reset_before = st.checkbox("Reset to original before applying", value=True)

                    if selected and st.button(f"Apply Selected Template", type="primary"):
                            tpl = load_template_from_disk(selected)
                            if not tpl:
                                st.error(f"Could not load template: {selected}")
                            else:
                                # Show any stored warnings prior to replay
                                warnings = replay_template(tpl, reset_first=reset_before, log_steps=True)
                                for w in warnings:
                                    st.warning(w)
                                st.success(f"Template replayed: {tpl.get('name', selected)}")
                                st.rerun()

        # Space between columns
        with col_break:
            st.write("")

        # Column on the right to display applied actions
        with col_actions:
            st.write("### Applied Actions")
            if st.session_state.applied_actions:
                for i, action in enumerate(reversed(st.session_state.applied_actions)):
                    with st.container():
                        st.write(f"**{len(st.session_state.applied_actions) - i}. {action['name']}**")
                        # st.write(f"_Applied at: {action['timestamp']}_")

                    # Specific undo button for each action type
                    if action['type'] == 'fix_concatenated':
                        if st.button(f"↶ Undo Fix", key=f"undo_fix_{action['id']}", type="secondary"):
                            undo_fix_concatenated_action(action['id'])
                            st.rerun()

                    elif action['type'] == 'apply_headers':
                        if st.button(f"↶ Undo Headers", key=f"undo_headers_{action['id']}", type="secondary"):
                            undo_choose_headers_action(action['id'])
                            st.rerun()
                    
                    elif action['type'] == 'remove_duplicates':
                        if st.button(f"↶ Undo Remove Duplicates", key=f"undo_duplicates_{action['id']}", type="secondary"):
                            undo_remove_duplicates_action(action['id'])
                            st.rerun()

                    elif action['type'] == 'apply_data_start':
                        if st.button(f"↶ Undo Apply Data Start", key=f"undo_data_start_{action['id']}", type="secondary"):
                            undo_data_start_action(action['id'])
                            st.rerun()

                    elif action['type'] == 'delete_unwanted_rows':
                        if st.button(f"↶ Undo Delete Unwanted Rows", key=f"undo_delete_{action['id']}", type="secondary"):
                            undo_delete_rows_action(action['id'])
                            st.rerun()

                    elif action['type'] == 'add_net_item_col':
                        if st.button(f"↶ Undo Add Item Net", key=f"undo_net_item_col_{action['id']}", type="secondary"):
                            undo_net_item_col_action(action['id'])
                            st.rerun()

            else:
                st.info("No actions applied yet")

        # Reset button to start over
        if st.button("Reset to Original", key="reset_btn", type="primary"):
            if all_tables:
                combined_table = pd.concat(all_tables, ignore_index=True)
                st.session_state.main_table = combined_table
                st.session_state.table_as_list = combined_table.values.tolist()
                st.session_state.working_data = combined_table.values.tolist()

                # Clear ALL session state variables including applied_actions
                for key in ['current_headers', 'raw_headers', 'header_row_index', 'applied_actions', 'data_start_index']:
                    if key in st.session_state:
                        del st.session_state[key]

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
