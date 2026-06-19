import os
import json
import sys

print("Checking dependencies...")
try:
    import pandas as pd
    import openpyxl
except ImportError:
    print("Error: 'pandas' or 'openpyxl' is not installed.", file=sys.stderr)
    print("Please install them by running: pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

files = {
    2022: "JU_Cutoff_2022.xlsx",
    2023: "JU_Cutoff_2023.xlsx",
    2024: "JU_Cutoff_2024.xlsx",
    2025: "Jadavpur_University_Cutoff_2025.xlsx"
}

summary = []
all_data = []

print("Reading Excel files...")
for year, filename in files.items():
    if not os.path.exists(filename):
        msg = f"File {filename} (year {year}) not found."
        print(msg)
        summary.append(msg)
        continue
    
    print(f"Processing {filename} for year {year}...")
    try:
        xl = pd.ExcelFile(filename)
        summary.append(f"\n=========================================")
        summary.append(f"FILE: {filename} (Year: {year})")
        summary.append(f"Sheets: {xl.sheet_names}")
        summary.append(f"=========================================")
        
        for sheet in xl.sheet_names:
            df = xl.parse(sheet)
            # Remove any fully empty rows
            df = df.dropna(how='all')
            summary.append(f"\nSheet '{sheet}' - Columns: {list(df.columns)}")
            summary.append(f"Total Rows: {len(df)}")
            if len(df) > 0:
                summary.append("Sample Data:")
                summary.append(df.head(3).to_string(index=False))
            
            # Convert rows to dicts
            df_dict = df.to_dict(orient='records')
            for row in df_dict:
                # Clean up keys and convert values
                cleaned_row = {}
                for k, v in row.items():
                    k_str = str(k).strip()
                    # Handle NaN values to make it JSON serializable
                    if pd.isna(v):
                        cleaned_row[k_str] = None
                    else:
                        cleaned_row[k_str] = v
                cleaned_row['__year'] = year
                cleaned_row['__sheet'] = sheet
                all_data.append(cleaned_row)
    except Exception as e:
        msg = f"Error reading {filename}: {str(e)}"
        print(msg)
        summary.append(msg)

# Write summary to a text file
summary_path = "columns_summary.txt"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write("\n".join(summary))
print(f"Summary written to '{summary_path}'")

# Write all raw data to a json file
json_path = "cutoff_data_raw.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2)
print(f"Raw cutoff data written to '{json_path}'")
print("\nConversion successfully completed! Please let the AI assistant know you have run it.")
