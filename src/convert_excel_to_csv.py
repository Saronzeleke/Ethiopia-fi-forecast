import pandas as pd
import os

def convert_excel_to_csv():
    """Convert Excel files to CSV format as required"""
    
    # 1. Convert main dataset (both sheets)
    excel_path =r'C:\Users\admin\Ethiopia-fi-forecast\data\raw\ethiopia_fi_unified_data.xlsx'
    
    # Read both sheets
    data_sheet = pd.read_excel(excel_path, sheet_name='ethiopia_fi_unified_data')
    impact_sheet = pd.read_excel(excel_path, sheet_name='Impact_sheet')
    
    # Combine both sheets (main dataset expects all records in one file)
    combined_data = pd.concat([data_sheet, impact_sheet], ignore_index=True)
    
    # Save to CSV
    combined_data.to_csv(r'C:\Users\admin\Ethiopia-fi-forecast\data\raw\ethiopia_fi_unified_data.csv', index=False)
    print(f"✅ Saved combined dataset with {len(combined_data)} records to CSV")
    
    # 2. Convert reference codes
    ref_excel_path =r'C:\Users\admin\Ethiopia-fi-forecast\data\raw\reference_codes.xlsx'
    ref_data = pd.read_excel(ref_excel_path, sheet_name='reference_codes')
    ref_data.to_csv(r'C:\Users\admin\Ethiopia-fi-forecast\data\raw\reference_codes.csv', index=False)
    print(f"✅ Saved reference codes with {len(ref_data)} records to CSV")
    
    # 3. Save guide as CSV for reference (optional)
    guide_excel_path =r'C:\Users\admin\Ethiopia-fi-forecast\data\raw\Additional Data Points Guide.xlsx'
    guide_sheets = ['A. Alternative Baselines', 'B. Direct Corrln', 
                   'C. Indirect Corrln', 'D. Market Naunces']
    
    for sheet in guide_sheets:
        try:
            guide_data = pd.read_excel(guide_excel_path, sheet_name=sheet)
            guide_data.to_csv(f'data/raw/guide_{sheet[:20]}.csv', index=False)
            print(f"✅ Saved guide sheet: {sheet}")
        except:
            print(f"⚠️ Could not read sheet: {sheet}")
    
    print("\n📊 Files created:")
    print("- data/raw/ethiopia_fi_unified_data.csv")
    print("- data/raw/reference_codes.csv")
    print("- data/raw/guide_*.csv (optional guide files)")

if __name__ == "__main__":
    convert_excel_to_csv()