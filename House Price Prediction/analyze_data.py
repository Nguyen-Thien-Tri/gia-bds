import pandas as pd
import numpy as np

def analyze():
    # Try reading the first few rows to get columns and check encoding
    try:
        # Based on the preview, it seems there's no header or the header is at line 0
        # Let's try reading with header=0
        df_sample = pd.read_csv('ads_data_2026_03.csv', nrows=5, encoding='utf-8')
    except UnicodeDecodeError:
        df_sample = pd.read_csv('ads_data_2026_03.csv', nrows=5, encoding='latin1')
    
    print("Columns found:")
    print(df_sample.columns.tolist())
    print("\nSample data:")
    print(df_sample.head())

if __name__ == "__main__":
    analyze()
