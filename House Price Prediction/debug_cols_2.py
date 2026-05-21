import pandas as pd

def debug():
    df = pd.read_csv('ads_data_2026_03.csv', nrows=2000, encoding='utf-8', encoding_errors='replace')
    
    with open('debug_output_2.txt', 'w', encoding='utf-8') as f:
        f.write("Column names and indices:\n")
        for i, col in enumerate(df.columns):
            f.write(f"{i}: {col}\n")
            
        f.write("\nUnique values in 'Loại BĐS' (first 2000 rows):\n")
        f.write(str(df[df.columns[6]].unique().tolist()))
        f.write("\nUnique values in 'Tỉnh thành phố' (first 2000 rows):\n")
        f.write(str(df[df.columns[7]].unique().tolist()))

if __name__ == "__main__":
    debug()
