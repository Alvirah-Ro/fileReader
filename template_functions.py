import streamlit as st
import json, os, re
from datetime import datetime, UTC

def build_template_from_actions(applied_actions):
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
            params = {a.get("params", {})}

        actions.append({"type": t, "params": params})

    return {
        "name": st.session_state.get("template_name", "Untitled"),
        "version": "K",
        "created_at": datetime.now(UTC).isoformat(),
        "actions": actions
    }
