"""
Template functions
"""


import streamlit as st
import json, os, re
from datetime import datetime, UTC

from table_functions import (choose_headers, apply_data_start,
                             fix_concatenated_table, update_display_table,
                             remove_duplicate_headers, delete_unwanted_rows,
                             add_net_item_col, save_action_state)


# Relative folder where all templates live 
# shared by anyone using same app instance
TEMPLATES_DIR = "templates" 

def action_label(action_type, params):
    if action_type == "apply_headers":
        return f"Headers from row {params.get('header_row_index')}"
    if action_type == "apply_data_start":
        return f"Data starts at row {params.get('data_start_index')}"
    if action_type == "remove_duplicates":
        return "Remove Duplicate Header Rows"
    if action_type == "fix_concatenated":
        return "Fix Concatenated Rows"
    if action_type == "delete_unwanted_rows":
        choice = params.get("choice")
        pat = params.get("pattern")
        label = choice if choice and choice != "other" else pat
        return f"Delete Rows: {label}"
    if action_type == "add_net_item_col":
        rp = params.get("retail_price_index")
        dp = params.get("discount_percent_index")
        # show 1-based to user
        return f"Add Item Net Column (price col {1+rp if rp is not None else '?'}, discount col {1+dp if dp is not None else '?'})"
    return action_type

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
    warnings = []
    tpl_actions = []
    for a in applied_actions:
        t= a["type"]
        p = a.get('params', {}) or {}
        
        # Use stored params first, then try current session state data if no stored params
        if t == "apply_headers":
            if "header_row_index" not in p:
                p = {"header_row_index": st.session_state.get("header_row_index")}
        elif t == "apply_data_start":
            if "data_start_index" not in p:
                p = {"data_start_index": st.session_state.get("data_start_index")}
        elif t == "remove_duplicates":
            if "header_row_index" not in p:
                p = {"header_row_index": st.session_state.get("header_row_index")}
        elif t == "fix_concatenated":
            p = {} # always empty
        elif t == "delete_unwanted_rows":
            if "pattern" not in p:
                warnings.append("Missing pattern for delete_unwanted_rows; step may be ineffective.")
                p = {} # Keep but note incomplete
        elif t == "add_net_item_col":
            if "retail_price_index" not in p or "discount_percent_index" not in p:
                p = {
                    "retail_price_index": st.session_state.get('retail_price_index'),
                     'discount_percent_index': st.session_state.get('discount_percent_index')
                }

        tpl_actions.append({"type": t, "params": p})

    return {
        "name": st.session_state.get("template_name", "Untitled"),
        "version": "K",
        "created_at": datetime.now(UTC).isoformat(),
        "actions": tpl_actions,
        "warnings": warnings
    }

def replay_template(tpl, reset_first=True, log_steps=True):
    """Accesses template and replays all steps to recreate the set table format"""
    if reset_first:
        # restore original
        st.session_state.working_data = [r[:] for r in st.session_state.original_table_data]
        st.session_state.current_headers = None
        st.session_state.header_row_index = None
        st.session_state.data_start_index = None
        update_display_table(st.session_state.working_data)

    warnings = []
    for step in tpl.get("actions", []):
        t = step["type"]
        p = step.get("params", {}) or {}

        # Log to Applied Actions before applying, so undo can restorepre-step state
        if log_steps:
            save_action_state(t, action_label(t, p), params=p)

        if t == "apply_headers":
            idx = p.get("header_row_index")
            if idx is None:
                warnings.append("Skipped apply_headers: missing index")
                continue
            choose_headers(idx)
            update_display_table(st.session_state.working_data)
        
        elif t == "apply_data_start":
            idx = p.get("data_start_index")
            if idx is None:
                warnings.append("Skipped apply_data_start: missing index")
                continue
            apply_data_start(idx) # sets index only
            update_display_table(st.session_state.working_data)

        elif t == "remove_duplicates":
            hdr_idx = p.get("header_row_index", st.session_state.get("header_row_index"))
            if hdr_idx is None:
                warnings.append("Skipped remove_duplicates: missing index")
                continue
            cleaned = remove_duplicate_headers(st.session_state.working_data, hdr_idx)
            update_display_table(cleaned)

        elif t == "fix_concatenated":
            fixed = fix_concatenated_table(st.session_state.working_data)
            update_display_table(fixed)

        elif t == "delete_unwanted_rows":
            pattern = p.get("pattern", "")
            if not pattern:
                warnings.append("Skipped delete_unwanted_rows: missing pattern")
                continue
            cleaned = delete_unwanted_rows(pattern)
            update_display_table(cleaned)

        elif t == "add_net_item_col":
            retail_idx = p.get("retail_price_index")
            discount_idx = p.get("discount_percent_index")
            if retail_idx is None or discount_idx is None:
                warnings.append("Skipped add_net_item_col: missing indices")
                continue
            added = add_net_item_col(retail_idx, discount_idx)
            update_display_table(added)
