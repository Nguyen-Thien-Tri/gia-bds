import pandas as pd

def check_filtered():
    df = pd.read_csv('filtered_hanoi_data.csv', nrows=10, encoding='utf-8')
    # Save a small sample to see it
    df.to_csv('sample_filtered.csv', index=False, encoding='utf-8')
    
    # Check nulls and types
    print("Columns and types:")
    print(df.dtypes)
    print("\nNull counts in key columns:")
    key_cols = ['Khoảng giá', 'Diên tích', 'Quận', 'Phường Xã Thị trấn', 'Loại BĐS']
    # Match the column names exactly as they are in the CSV
    print(df.columns.tolist())

if __name__ == "__main__":
    check_filtered()
