"""
Template functions
"""


import streamlit as st
import json, os, re
from datetime import datetime, UTC

from table_functions import (save_action_state, choose_headers, undo_choose_headers_action, apply_data_start,
                             undo_data_start_action, fix_concatenated_table, undo_fix_concatenated_action,
                             update_display_table, remove_duplicate_headers, undo_remove_duplicates_action,
                             delete_unwanted_rows, undo_delete_rows_action)


# Relative folder where all templates live 
# shared by anyone using same app instance
TEMPLATES_DIR = "templates" 


def ensure_templates_dir():
    """Create a templates directory if it doesn't already exist"""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

def sanitize_filename(name):
    """Strips unsafe characters from user-entered template name so it's safe as a filename"""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "template"

def save_template_to_disk(tpl):
    """Builds a filename and writes it to disk"""
    ensure_templates_dir()
    fname = sanitize_filename(tpl["name"]) + ".json"
    path = os.path.join(TEMPLATES_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tpl, f, ensure_ascii=False, indent=2)
    return path

def list_templates():
    "Returns all files in templates ending with .json"
    ensure_templates_dir()
    return [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".json")]

def load_template_from_disk(filename):
    """Opens templates and loads it to a Python dict to replay actions in order"""
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_template_from_actions(applied_actions):
    """Build a template from current state"""
    actions = []
    for a in applied_actions:
        t= a["type"]
        params = {}

        if t == "apply_headers":
            params = {"header_row_index": st.session_state.get("header_row_index")}
        elif t == "apply_data_start":
            params = {"data_start_index": st.session_state.get("data_start_index")}
        elif t == "remove_duplicates":
            params = {"header_row_index": st.session_state.get("header_row_index")}
        elif t == "delete_unwanted_rows":
            params = {a.get("params", {})} # Store as a dictionary

        actions.append({"type": t, "params": params})

    return {
        "name": st.session_state.get("template_name", "Untitled"),
        "version": "K",
        "created_at": datetime.now(UTC).isoformat(),
        "actions": actions
    }

def replay_template(tpl, reset_first=True, log_steps=False):
    """Accesses template and replays all steps to recreate the set table format"""
    if reset_first:
        # restore original
        st.session_state.working_data = st.session_state.original_table_data.copy()
        st.session_state.current_headers = None
        st.session_state.header_row_index = None
        st.session_state.data_start_index = None
        update_display_table(st.session_state.working_data)

    for step in tpl["actions"]:
        t = step["type"]
        p = step.get("params", {})

        if t == "apply_headers":
            idx = p.get("header_row_index")
            choose_headers(idx)
            update_display_table(st.session_state.working_data)
        
        elif t == "apply_data_start":
            idx = p.get("data_start_index")
            apply_data_start(idx) # sets index only
            update_display_table(st.session_state.working_data)

        elif t == "remove_duplicates":
            hdr_idx = p.get("header_row_index", st.session_state.get("header_row_index"))
            cleaned = remove_duplicate_headers(st.session_state.working_data, hdr_idx)
            update_display_table(cleaned)

        elif t == "fix_concatenated":
            fixed = fix_concatenated_table(st.session_state.working_data)
            update_display_table(fixed)

        elif t == "delete_unwanted_rows":
            pattern = p.get("pattern", "")
            cleaned = delete_unwanted_rows(pattern)
            update_display_table(cleaned)

        if log_steps:
            # optionally add entries to applied_actions
            pass