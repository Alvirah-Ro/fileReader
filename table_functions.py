"""
Table processing functions
"""

import pandas as pd

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
