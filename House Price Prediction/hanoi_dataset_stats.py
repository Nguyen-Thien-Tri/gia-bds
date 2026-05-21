import pandas as pd
import io
import sys

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    file_path = 'filtered_hanoi_data.csv'
    print(f"Reading dataset: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    with open('hanoi_stats_output.txt', 'w', encoding='utf-8') as f:
        f.write(f"Dataset Statistics for {file_path}\n")
        f.write("="*50 + "\n\n")
        
        f.write(f"1. Basic Information\n")
        f.write("-" * 20 + "\n")
        f.write(f"Number of rows: {df.shape[0]}\n")
        f.write(f"Number of columns: {df.shape[1]}\n\n")
        
        f.write("2. Columns and Data Types\n")
        f.write("-" * 20 + "\n")
        for col, dtype in df.dtypes.items():
            f.write(f"- {col}: {dtype}\n")
        f.write("\n")
        
        f.write("3. Missing Values\n")
        f.write("-" * 20 + "\n")
        missing_counts = df.isnull().sum()
        for col, missing in missing_counts.items():
            f.write(f"- {col}: {missing} missing values ({(missing/df.shape[0])*100:.2f}%)\n")
        f.write("\n")
        
        f.write("4. Summary Statistics (Numeric)\n")
        f.write("-" * 20 + "\n")
        f.write(df.describe().to_string())
        f.write("\n\n")
        
        f.write("5. Summary Statistics (Categorical)\n")
        f.write("-" * 20 + "\n")
        cat_cols = df.select_dtypes(include=['object']).columns
        if len(cat_cols) > 0:
            f.write(df[cat_cols].describe().to_string())
        f.write("\n")

    print("Statistics successfully saved to hanoi_stats_output.txt")

if __name__ == '__main__':
    main()
