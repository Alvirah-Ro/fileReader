"""
Template functions
"""

from datetime import datetime, UTC
import json
import os
import re
import streamlit as st


from table_functions import (choose_headers, fix_concatenated_table,
                             update_display_table, remove_duplicate_headers,
                             delete_unwanted_rows, add_net_item_col,
                             save_action_state)


# Relative folder where all templates live 
# shared by anyone using same app instance
TEMPLATES_DIR = "templates" 

# Single registry describing each action
# - required: params that must be present (if missing: back-fill from session_state)
# - label: a format string using keys from params (add +1 for 1-based indices)
# - func: the callable to execute
# - args: list of argument specs; taken from params or working_data
# - returns_data: True if func returns new list-of-rows to render, otherwise just post_update
# -post_update: call update_display_table even if function returns None (for stateful funcs)
ACTIONS = {
    "apply_headers": {
        "required": ["header_row_index"],
        "label": "Headers from row {header_row_index}",
        "func": choose_headers,
        "args": ["header_row_index"],
        "returns_data": False,
        "post_update": True,
    },
    "remove_duplicates": {
        "required": ["header_row_index"],
        "label": "Remove Duplicate Header Rows",
        "func": remove_duplicate_headers,
        "args": ["working_data", "header_row_index"],
        "returns_data": True,
        "post_update": False,
    },
    "fix_concatenated": {
        "required": [],
        "label": "Fix Concatenated Rows",
        "func": fix_concatenated_table,
        "args": ["working_data"],
        "returns_data": True,
        "post_update": False,
    },
    "delete_unwanted_rows": {
        "required": ["pattern"],
        "label": "Delete Rows: {pattern}",
        "func": delete_unwanted_rows,
        "args": ["pattern"],
        "returns_data": True,
        "post_update": False,
    },
    "add_net_item_col": {
        "required": ["retail_price_index", "discount_percent_index"],
        "label": lambda p: (
            f"Add Item Net Column (price col {1 + p['retail_price_index'] if p.get('retail_price_index') is not None else '?'}, "
            f"discount col {1 + p['discount_percent_index'] if p.get('discount_percent_index') is not None else '?'})"
        ),
        "func": add_net_item_col,
        "args": ["retail_price_index", "discount_percent_index"],
        "returns_data": True,
        "post_update": False,
    },
}

def action_label(action_type, params):
    """
    Builds a human-readable label for an action using ACTIONS registry
    Supports labels defined as format strings or callables.
    """
    cfg = ACTIONS.get(action_type) # cfg is short for configuration: a small dict describing how to handle actions
    if not cfg:
        return action_type
    label = cfg.get("label")
    try:
        if callable(label):
            return label(params or {})
        # label is a format string; format with params
        return str(label).format(**(params or {}))
    except Exception:
        # Fallback if formatting errors occur
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
    ss = st.session_state

    for a in applied_actions:
        t= a["type"]
        p = dict(a.get("params", {}) or {})
        cfg = ACTIONS.get(t)
        if not cfg:
            warnings.append(f"Unknown action type in build: {t}")
            tpl_actions.append({"type": t, "params": p})
            continue

        # Backfill required params from session_state if missing
        for req in cfg["required"]:
            if p.get(req) is None: # missing in saved params
                p[req] = ss.get(req) # try session fallback
            if p.get(req): # still missing after fallback
                warnings.append(f"Missing {req} for {t}")
        
        tpl_actions.append({"type": t, "params": p})

    return {
        "name": ss.get("template_name", "Untitled"),
        "version": "K",
        "created_at": datetime.now(UTC).isoformat(),
        "actions": tpl_actions,
        "warnings": warnings,
    }

def _invoke(cfg, params):
    """Small dispatcher to execute action's function based on entry in ACTIONS"""
    func = cfg["func"]
    args = []
    for spec in cfg["args"]:
        if spec == "working_data":
            args.append(st.session_state.working_data)
        else:
            args.append(params.get(spec))
    try:
        result = func(*args)
        return result, []
    except Exception as e:
        return None, [f"Error invoking {getattr(func, '__name__', 'action')}: {e}"]

def replay_template(tpl, reset_first=True, log_steps=True):
    """Accesses template and replays all steps to recreate the set table format"""
    warnings = []
    if reset_first:
        # restore original
        st.session_state.working_data = [r[:] for r in st.session_state.original_table_data]
        st.session_state.current_headers = None
        st.session_state.header_row_index = None
        update_display_table(st.session_state.working_data)

    for step in tpl.get("actions", []):
        t = step["type"]
        p = step.get("params", {}) or {}
        cfg = ACTIONS.get(t)
        if not cfg:
            warnings.append(f"Unknown action during replay: {t}")
            continue

        # Log to Applied Actions so Undo works per-step
        if log_steps:
            save_action_state(t, action_label(t, p), params=p)

        # Validate required params
        missing = [req for req in cfg["required"] if p.get(req) is None]
        if missing:
            warnings.append(f"Skipped {t}: missing {', '.join(missing)}")
            continue

        result, call_warnings = _invoke(cfg, p)
        warnings.extend(call_warnings)

        if cfg["returns_data"]:
            if result is None:
                warnings.append(f"{t} returned no data")
            else:
                update_display_table(result)
        elif cfg.get("post_update"):
            update_display_table(st.session_state.working_data)
    
    return warnings
