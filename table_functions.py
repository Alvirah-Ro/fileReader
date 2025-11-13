"""
Table processing functions
"""

import streamlit as st
import uuid
from datetime import datetime


def save_action_state(action_type, action_name):
    """Save current state before applying an action"""
    action_id = str(uuid.uuid4())[:8]
    action_data= {
        'id': action_id,
        'type': action_type,
        'name': action_name,
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'working_data': st.session_state.working_data.copy(),
        'current_headers': st.session_state.get('current_headers', None),
        'main_table': st.session_state.main_table.copy() if 'main_table' in st.session_state else None
    }
    st.session_state.applied_actions.append(action_data)
    return action_id


def fix_concatenated_table(table):
    """Fix tables where PDFPlumber concatenates column data"""

    # For example: if every row of data in a column is showing up in 1 cell
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


def undo_fix_concatenated_action(action_id):
    """Undo specific fix concatenated action"""
    action_index = next(i for i, action in enumerate(st.session_state.applied_actions) if action['id'] == action_id)
    target_action = st.session_state.applied_actions[action_index]

    # Restore state from before this action
    st.session_state.working_data = target_action['working_data']
    st.session_state.current_headers = target_action['current_headers']
    if target_action['main_table'] is not None:
        st.session_state.main_table = target_action['main_table']
    
    # Remove this action and all subsequent actions
    st.session_state.applied_actions = st.session_state.applied_actions[:action_index]
    
    st.success(f"Undone: {target_action['name']} and all subsequent actions")
    st.rerun()


def clean_duplicate_headers(headers):
    """Clean duplicate headers by appending numbers to duplicates"""
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


def undo_headers_action(action_id):
    """Undo specific headers action"""
    action_index = next(i for i, action in enumerate(st.session_state.applied_actions) if action['id'] == action_id)
    target_action = st.session_state.applied_actions[action_index]

    # Restore state from before this action
    st.session_state.working_data = target_action['working_data']
    st.session_state.current_headers = target_action['current_headers']
    if target_action['main_table'] is not None:
        st.session_state.main_table = target_action['main_table']
    
    # Remove this action and all subsequent actions
    st.session_state.applied_actions = st.session_state.applied_actions[:action_index]
    
    st.success(f"Undone: {target_action['name']} and all subsequent actions")
    st.rerun()
