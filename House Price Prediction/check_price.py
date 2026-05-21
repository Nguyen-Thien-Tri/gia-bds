import pandas as pd
import numpy as np

def check_price():
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    col_price = 'Khoảng giá'
    col_area = 'Diện tích'
    
    # Convert to numeric
    prices = pd.to_numeric(df[col_price], errors='coerce').dropna()
    areas = pd.to_numeric(df[col_area], errors='coerce').dropna()
    
    with open('price_debug.txt', 'w', encoding='utf-8') as f:
        f.write(f"Price stats:\n{prices.describe().to_string()}\n")
        f.write(f"\nSmallest prices:\n{prices.sort_values().head(50).to_string()}\n")
        f.write(f"\nLargest prices:\n{prices.sort_values(ascending=False).head(50).to_string()}\n")
        
        # Check price per m2
        common_indices = prices.index.intersection(areas.index)
        ppm = prices[common_indices] / areas[common_indices]
        f.write(f"\nPrice per m2 stats:\n{ppm.describe().to_string()}\n")
        f.write(f"\nSmallest PPM:\n{ppm.sort_values().head(50).to_string()}\n")
        f.write(f"\nLargest PPM:\n{ppm.sort_values(ascending=False).head(50).to_string()}\n")

if __name__ == "__main__":
    check_price()
