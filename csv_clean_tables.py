import streamlit as st
import pandas as pd
import re

st.title('Clean CSV Table with Separated Columns')

# Read the CSV
st.title("CSV Table Viewer")

uploaded_file = st.file_uploader("Upload CSV File", type="csv")

if uploaded_file is not None:
    # Read the CSV
    df = pd.read_csv(uploaded_file)

    st.write("**Original (messy) data:**")
    st.dataframe(df)

    # Get the column name (probably something like "Edition # Location Title...")
    col_name = df.columns[0]

    # Split each row into proper columns
    cleaned_rows = []
    headers = ['Edition', 'Location', 'Title', 'Order', 'Ship', 'BO', 'List', 'Disc', 'Net', 'Extension']

    for idx, row_data in df.iterrows():
        if idx > 0: # Skip the header row since it's mixed in with data

        text = str(row_data[col_name])

         # Split by multiple spaces (2 or more spaces usually separate columns)
        parts = re.split(r'\s{2,}', text)
        parts = [p.strip() for p in parts if p.strip()]

        st.write(f"There are {len(parts)} parts.  Here they are:", parts)

        # If we have enough parts, this looks like a valid row
        if len(parts) >=6: # At least Edition, Title, and some numbers
            cleaned_rows.append(parts)

        st.write("the cleaned rows are:", cleaned_rows)

    # Create clean DataFrame
    if cleaned_rows:
        # Find max columns
        max_cols = max(len(row) for row in cleaned_rows)

        #Pad shorter rows
        padded_rows = []
        for row in cleaned_rows:
            padded_row = row + [''] * (max_cols - len(row))
            padded_rows.append(padded_row)

        # Use appropriate headers
        column_names = headers[:max_cols]
        if max_cols > len(headers):
            column_names.extend([f'Col_{i}' for i in range(len(headers), max_cols)])
        
        clean_df = pd.DataFrame(padded_rows, columns=column_names)

        st.write("**Cleaned data with separated columns:**")
        st.dataframe(clean_df, width="stretch")

        # Show summary
        st.write(f"**Success!** Extracted {len(clean_df)} items with {len(clean_df.columns)} columns")

        # Download clean version
        clean_csv = clean_df.to_csv(index=False)
        st.download_button("Download Clean Table", clean_csv, "invoice_items_clean.csv")
    
    else:
        st.error("Could not parse the data into columns")

else:
    st.write("Please download a CSV file")