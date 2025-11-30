"""
Undo Table processing functions
"""

import streamlit as st

def undo_choose_headers_action(action_id):
    """Undo choose headers action"""

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


def undo_remove_duplicates_action(action_id):
    """Undo specific remove duplicates action"""

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


def undo_delete_rows_action(action_id):
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


def undo_net_item_col_action(action_id):
    """Undo specific add item net column"""
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
