import pandas as pd

def debug():
    df = pd.read_csv('ads_data_2026_03.csv', nrows=1000, encoding='utf-8', encoding_errors='replace')
    
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        f.write("Column names and indices:\n")
        for i, col in enumerate(df.columns):
            f.write(f"{i}: {col}\n")
        
        # Search for Hanoi in all columns
        for col in df.columns:
            if df[col].astype(str).str.contains('Hà Nội').any():
                f.write(f"Found 'Hà Nội' in column: {col} (Index: {df.columns.get_loc(col)})\n")
                
        # Search for property types
        target_types = ["Căn hộ chung cư", "Nhà mặt phố", "Nhà riêng", "Đất"]
        for col in df.columns:
            if df[col].isin(target_types).any():
                f.write(f"Found property types in column: {col} (Index: {df.columns.get_loc(col)})\n")

if __name__ == "__main__":
    debug()
