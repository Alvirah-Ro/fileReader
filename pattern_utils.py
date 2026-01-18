import re
from typing import Optional

# Reusable mappings for row/column deletion
# the -> in a function signature is a return type hint

EMPTY_PATTERN = r"^\s*$" # empty or whitespace-only

def build_word_pattern(word: str, contains: bool = True, whole_word: bool = True, case_insensitive: bool = True) -> str:
    w = re.escape((word or "").strip())
    if not w:
        return EMPTY_PATTERN
    prefix = "(?i)" if case_insensitive else ""
    if contains:
        if whole_word:
            return rf"{prefix}\b{w}\b"
        return rf"{prefix}{w}"
    # exact match (allow leading/trailing space in the cell)
    return rf"{prefix}^\s*{w}\s*$"

def build_number_pattern(digits: int, contains: bool = True) -> str:
    d = max(1, int(digits or 1))
    if contains:
        # contains a number token of exactly N digits
        return rf"(?<!\d)\d{{{d}}}(?!\d)"
    # entire cell is exactly N digits (with surrounding space allowed)
    return rf"^\s*\d{{{d}}}\s*$"

def build_symbols_pattern(contains: bool = True) -> str:
    # symbols = any char that is not letter/number/underscore or whitespace
    base = r"[^\w\s]+"
    if contains:
        return base # search anywhere in cell
    return rf"^\s*{base}\s*$" # cell is only symbols

def resolve_delete_pattern(
        choice: str,
        *,
        word: Optional[str] = None,
        digits: Optional[int] = None,
        use_whole_word: bool = True,
        case_insensitive: bool = True,
        contains: bool = True,
        custom: Optional[str] = None,
        custom_is_regex: bool = True
) -> Optional[str]:
    """
    Returns a regex string for the given choice and parameters.
    If inputs are missing, returns None so the UI can show an error.
    """
    if choice == "Empty space":
        return EMPTY_PATTERN
    if choice == "Numbers (N digits)":
        if digits is None:
            return None
        return build_number_pattern(digits=int(digits), contains=contains)
    if choice == "Symbols (contains)":
        return build_symbols_pattern(contains=True)
    if choice == "Word (contains)":
        if not word:
            return None
        return build_word_pattern(word, contains=True, whole_word=use_whole_word, case_insensitive=case_insensitive)
    if choice == "Word (exact)":
        if not word:
            return None
        return build_word_pattern(word, contains=False, whole_word=True, case_insensitive=case_insensitive)
    if choice == "Other":
        if not custom or not custom.strip():
            return None
        return custom.strip() if custom_is_regex else re.escape(custom.strip())
    # Unknown choice
    return None
    
