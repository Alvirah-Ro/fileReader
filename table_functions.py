"""
Table processing functions
"""

import uuid
from datetime import datetime
import re
import streamlit as st
import pandas as pd


def save_action_state(action_type, action_name, params=None):
    """Save current state before applying an action"""
    action_id = str(uuid.uuid4())[:8]
    action_data= {
        'id': action_id,
        'type': action_type,
        'name': action_name,
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'params': params or {}, # store parameters here
        'working_data': [r[:] for r in st.session_state.working_data] if 'working_data' in st.session_state else None,
        'current_headers': list(st.session_state.current_headers) if st.session_state.get('current_headers') else None,
        'header_row_index': st.session_state.get('header_row_index'),
        'main_table': st.session_state.main_table.copy(deep=True) if 'main_table' in st.session_state else None,

    }
    st.session_state.applied_actions.append(action_data)
    return action_id

def update_display_table(new_working_data):
    """
    Build DataFrame from working_data while hiding the header source row (if chosen).
    """
    # Update working data
    st.session_state.working_data = new_working_data
    header_row_idx = st.session_state.get("header_row_index")
    headers_to_use = st.session_state.get("current_headers")

    # Hide header row without mutating working data
    if header_row_idx is not None and 0<= header_row_idx < len(new_working_data):
        display_rows = [r for i, r in enumerate(new_working_data) if i != header_row_idx]
    else:
        display_rows = new_working_data

    # Header length guard
    if headers_to_use and display_rows and len(headers_to_use) != len(display_rows[0]):
        headers_to_use = None

    # Update display
    st.session_state.main_table = pd.DataFrame(display_rows, columns= headers_to_use)

def to_float(value, default=0.0):
    """
    Convert mixed numeric cell content to float.
    Handles: commas, %, currency symbols, parentheses for negatives.
    Returns default (0.0) on failure
    """
    if value is None:
        return default
    s = str(value).strip()
    if not s:
        return default
    # Handle negative parentheses: (123.45) -> -123.45
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    # Remove common noise
    for ch in ["$", "£", "€", ","]:
        s = s.replace(ch, "")
    s = s.replace("%", "")
    # Final clean
    try:
        num = float(s)
        return -num if neg else num
    except:
        return default


def clean_duplicate_headers(headers):
    """
    Clean duplicate headers by appending numbers to duplicates
    This function is used in choose_headers function
    """

    clean_headers = [] # Store final cleaned header names
    seen_headers = {} # Track how many times each header appears

    for header in headers:
        # Convert to string and handle None/empty values
        if header is None or header == '' or str(header).strip() == '':
            header = "Unnamed"
        else:
            header = str(header).strip()

        # Handle duplicates
        if header in seen_headers:
            seen_headers[header] += 1
            unique_header = f"{header}_{seen_headers[header]}" # Add number suffix
        else:
            seen_headers[header] = 0
            unique_header = header # Keep original name
        
        clean_headers.append(unique_header)

    return clean_headers

def choose_headers(header_row_input):
    """Apply headers from specified row without changing data start"""
    current_data = st.session_state.working_data

    # Extract and clean headers
    raw_headers = current_data[header_row_input]
    clean_headers = clean_duplicate_headers(raw_headers) 

    # Store header info in session state
    st.session_state.current_headers = clean_headers
    st.session_state.raw_headers = raw_headers
    st.session_state.header_row_index = header_row_input

    return clean_headers


def remove_duplicate_headers(table_data, header_row_index):
    """
    Remove duplicate header rows from table data
    Keeps first occurrence of header row and removes subsequent duplicates
    """
    if not table_data or header_row_index >= len(table_data):
        return table_data

    header_row = table_data[header_row_index]
    cleaned_data = []

    for i, row in enumerate(table_data):
        # Keep the original header row and all rows that don't match it
        if i == header_row_index or row != header_row:
            cleaned_data.append(row)

    return cleaned_data


def fix_concatenated_table(table):
    """Fix tables where PDFPlumber concatenates column data, preserving header row unchanged."""
    # For example: if every row of data in a column is showing up in 1 cell
    if  not table or len(table) < 2:
        return table
    
    header_row_idx = st.session_state.get("header_row_index")
    fixed_rows = []
    # Process each row
    for i, row in enumerate(table):
        #Preserve header row (do not split)
        if header_row_idx is not None and i == header_row_idx:
            fixed_rows.append(row[:])
            continue
        
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


def delete_unwanted_rows(search_pattern):
    """Delete rows that don't contain actual data - pick by input"""
    kept_rows = []
    matched_rows = []
    
    for i, row in enumerate(st.session_state.working_data):
        # Check if the first cell in the row matches the pattern
        first_cell = str(row[0]) if row and row[0] is not None else ""
        if re.search(search_pattern, first_cell):
            matched_rows.append((i, first_cell))
        else:
            kept_rows.append(row)

    # Store matches in session state to show later
    if matched_rows:
        st.session_state.debug_matches = matched_rows

    return kept_rows


def add_net_item_col(retail_idx, discount_idx, header_name="Item Net"):
    """
    Insert a net column (price * (1 - discount%)) immediately after the discount column
    Indices are zero-based.  Returns the updated working_data (list of rows).
    """

    if not st.session_state.working_data:
        return st.session_state.working_data # Nothing to do if empty
    # max_width = max((len(r) for r in st.session_state.working_data), default=0)
    
    # Validate indices
    if any(v is None for v in (retail_idx, discount_idx)) or retail_idx < 0 or discount_idx < 0:
        return st.session_state.working_data
    
    net_item_values = []
    for row in st.session_state.working_data:
        if len(row) <= max(retail_idx, discount_idx):
            net_item_values.append("")
            continue
        price = to_float(row[retail_idx])
        disc_percent = to_float(row[discount_idx])
        net = price * (1 - disc_percent / 100)
        net_item_values.append(f"{net:.2f}")

    # Insert after discount column
    insert_position = discount_idx + 1
    for i, row in enumerate(st.session_state.working_data):
        if len(row) < insert_position:
            row.extend([""] * (insert_position - len(row)))
        row.insert(insert_position, net_item_values[i])
                        
    if st.session_state.get("current_headers"):
        headers = st.session_state.current_headers
        # Pad headers up to insert_position
        while len(headers) < insert_position:
            headers.append(f"col_{len(headers)}")
        # Insert new header
        headers.insert(insert_position, header_name)
        # Reconcile header count with widest row
        new_width = max((len(r) for r in st.session_state.working_data), default=0)
        while len(headers) < new_width:
            headers.append(f"col_{len(headers)}")
        if len(headers) > new_width:
            headers[:] = headers[:new_width]

    return st.session_state.working_data

