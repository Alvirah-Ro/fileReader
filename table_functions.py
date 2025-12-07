"""
Table processing and template functions
"""

import uuid
from datetime import datetime, UTC
import json
import os
import re
import streamlit as st
import pandas as pd

# Relative folder where all templates live 
# shared by anyone using same app instance
TEMPLATES_DIR = "templates" 

def save_action_state(action_type, action_name=None, params=None):
    """Save current state before applying an action"""
    # Compute label from ACTIONS registry if not provided
    label = action_name or action_label(action_type, params or {})
    action_id = str(uuid.uuid4())[:8]
    action_data= {
        'id': action_id,
        'type': action_type,
        'params': params or {}, # store parameters here
        'label': label,
        'name': action_name,
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'working_data': [r[:] for r in st.session_state.working_data] if 'working_data' in st.session_state else None,
        'current_headers': list(st.session_state.current_headers) if st.session_state.get('current_headers') else None,
        'header_row_index': st.session_state.get('header_row_index'),
        'main_table': st.session_state.main_table.copy(deep=True) if 'main_table' in st.session_state else None,
    }
    st.session_state.setdefault('applied_actions', []).append(action_data)
    # Invalidate redo on any new forward action
    st.session_state['redo_stack'] = []
    return action_id

def update_display_table(new_working_data):
    """
    Build DataFrame from working_data while hiding the header source row (if chosen).
    """
    # Update working data
    st.session_state.working_data = new_working_data
    header_row_idx = st.session_state.get("header_row_index")
    headers_to_use = st.session_state.get("current_headers")
    raw_headers = st.session_state.get("raw_headers")

    # Hide header row without mutating working data
    display_rows = []
    for i, r in enumerate(new_working_data):
        if header_row_idx is not None and i == header_row_idx:
            continue
        if raw_headers is not None and r == raw_headers:
            continue
        display_rows.append(r)

    # Header length guard
    if headers_to_use and display_rows and len(headers_to_use) != len(display_rows[0]):
        headers_to_use = None

    # Update display
    st.session_state.main_table = pd.DataFrame(display_rows, columns= headers_to_use)

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
    
    raw_headers = st.session_state.get("raw_headers")
    fixed_rows = []
    # Process each row
    for i, row in enumerate(table):
        #Preserve header row (do not split)
        if raw_headers is not None and row == raw_headers:
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

def _invoke(cfg, params):
    """Dispatcher to execute action's function based on entry in ACTIONS."""
    func = cfg["func"]
    specs = cfg["args"]

    # Find actions that consume working_data
    uses_working = any(spec == "working_data" for spec in specs)
    ss = st.session_state
    raw_headers = ss.get("raw_headers")
    header_idx = ss.get("header_row_index")
    rows = ss.get("working_data", [])

    # If action uses working_data and a header row is selected,
    # run the transform on data-only rows (exclude header), then reinsert header unchanged.
    if uses_working and rows and header_idx is not None:
        protected = [(i, r) for i, r in enumerate(rows) if r == raw_headers]
        if protected:
            protected_indices = {i for i, _ in protected}
            data_only = [
                r for i, r in enumerate(rows) if i not in protected_indices]

            # Build args, substituting data_only for working_data
            call_args = []
            for spec in specs:
                if spec == "working_data":
                    call_args.append(data_only)
                else:
                    call_args.append(params.get(spec))
            try:
                result = func(*call_args)
                # If the action returns data, reinsert the header at (min) original index
                if cfg["returns_data"]:
                    out = result or data_only
                    hdr_row = protected[0][1][:]
                    insert_at = header_idx if header_idx is not None else protected[0][0]
                    insert_at = max(0, min(insert_at, len(out)))
                    out = out[:insert_at] + [hdr_row] + out[insert_at:]
                    return out, []
                return result, []
            except Exception as e:
                return None, [f"Error invoking {getattr(func, '__name__', 'action')}: {e}"]
        
    # Normal path (no header protection needed)
    call_args = []
    for spec in specs:
        if spec == "working_data":
            call_args.append(ss.get("working_data", []))
        else:
            call_args.append(params.get(spec))
    try:
        result = func(*call_args)
        return result, []
    except Exception as e:
        return None, [f"Error invoking {getattr(func, '__name__', 'action')}: {e}"]
    
def run_action(action_type, params):
    """
    Use the ACTIONS registry to run all functions, update display,
    and log into Applied Actions once.
    """
    cfg = ACTIONS.get(action_type)
    if not cfg:
        st.warning(f"Unknown action: {action_type}")
        return
    
    # Validate required params
    missing = [req for req in cfg["required"] if params.get(req) is None]
    if missing:
        st.warning(f"Missing {', '.join(missing)} for {action_type}")
        return
    
    # Log once
    save_action_state(action_type, action_label(action_type, params), params=params)

    # 'invoke and render
    result, warnings = _invoke(cfg, params)
    for w in warnings:
        st.warning(w)

    if cfg["returns_data"]:
        if result is not None:
            update_display_table(result)
        else:
            st.warning(f"{action_type} returned no data")
    elif cfg.get("post_update"):
        update_display_table(st.session_state.working_data)

def reset_all():
    """
    Reset everything to the initial state
    - restore working_data from original_table_data
    - clear headers/state flags
    - clear applied actions_and redo_stack
    - rebuild main_table
    """
    # Restore original data
    original = [r[:] for r in st.session_state.get('original_table_data', [])]
    st.session_state.working_data = original

    # Clear common state flags
    for key in [
        "current_headers",
        "header_row_index",
    ]:
        st.session_state.pop(key, None)

    # Clear history
    st.session_state['applied_actions'] = []
    st.session_state['redo_stack'] = []

    # Re-render
    st.session_state.main_table = pd.DataFrame(st.session_state.working_data, columns=None)

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
            if p.get(req) is None: # still missing after fallback
                warnings.append(f"Missing {req} for {t}")
        
        tpl_actions.append({"type": t, "params": p})

    return {
        "name": ss.get("template_name", "Untitled"),
        "version": "K",
        "created_at": datetime.now(UTC).isoformat(),
        "actions": tpl_actions,
        "warnings": warnings,
    }

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

def replay_from_actions(actions, reset_first=True, log_steps=False):
    """
    Recompute state by replaying a plain actions list using replay_template.
    Use to help undo last action.
    """
    tpl = {
        "name": "_replay_from_actions",
        "version": "K",
        "created_at": datetime.now(UTC).isoformat(),
        "actions": actions,
        "warnings": [],
    }
    return replay_template(tpl, reset_first=reset_first, log_steps=log_steps)

def undo_last_action():
    """Removes last action and replays list of actions without it"""
    actions = st.session_state.get('applied_actions', [])
    if not actions:
        return False
    last = actions.pop()
    st.session_state.redo_stack.append(last) # Push to redo
    st.session_state.applied_actions = actions
    # Recompute from original without logging
    replay_from_actions(
        actions=[{'type': a['type'], 'params': a.get('params', {}) or {}} for a in actions],
        reset_first=True,
        log_steps=False # Don't log steps to avoid duplicating history
    )
    return True

def undo_to_action_id(action_id):
    """Undo to a specific point, not always the last step"""
    actions = st.session_state.get('applied_actions', [])
    if not actions:
        return False
    
    idx = next((i for i, a in enumerate(actions) if a.get('id') == action_id), None)
    if idx is None:
        return False
    
    # Move removed actions to redo_stack (in order)
    removed = actions[idx:] # target and all after
    # Put target action on top of redo stack by pushing in reverse order
    for a in reversed(removed):
        st.session_state.redo_stack.append(a)

    # Keep the actions before target
    kept = actions[:idx]
    st.session_state.applied_actions = kept

    # Replay the kept actions only
    replay_from_actions(
        actions=[{'type': a['type'], 'params': a.get('params', {}) or {}} for a in kept],
        reset_first=True,
        log_steps=False # Don't log steps to avoid duplicating history
    )
    return True

def redo_last_action():
    """Redo the most recent undone action."""
    stack = st.session_state.get('redo_stack', [])
    if not stack:
        return False
    action = stack.pop() # redo one
    st.session_state.applied_actions.append(action)
    # Apply just this action on top of the current state (no logging duplication)
    replay_from_actions(
        actions=[{'type': action['type'], 'params': action.get('params', {}) or {}}],
        reset_first=False,
        log_steps=False
    )
    return True
