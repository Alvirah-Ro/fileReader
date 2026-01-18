import re
from typing import Optional

# Reusable regex/text mappings for row/column deletion
DELETE_VALUE_MAPPING = {
    "Empty": r"^\s*$",  # empty or whitespace-only
    "Letters": r"^[A-Za-z\s]+$",  # only letters and spaces
    "Numbers": r"^[\d\s.,]+$",  # only numbers, spaces, commas, periods
    "Symbols": r"^[^\w\s]+$",  # only symbols (no letters or numbers)
    "Word: None": r"(?i)^\s*None\s*$", # literal word 'None' (case-insensitive)
}
