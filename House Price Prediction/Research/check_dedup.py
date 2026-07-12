import pandas as pd
import numpy as np

def debug_groupby():
    print("Loading data...")
    # Read the full filtered data
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    top_4_types = ['căn hộ chung cư', 'nhà riêng', 'đất', 'nhà mặt phố']
    df = df[(df['Loại quảng cáo'] == 'Bán') & (df['Loại BĐS'].isin(top_4_types))].copy()
    
    # We will need Khoảng giá and Diện tích to be numeric to do the dropna logic
    # But wait, in Notebook approach, Khoảng giá and Diện tích are NOT coerced aggressively for other columns.
    # To keep the test focused strictly on the difference between string vs numeric for the grouping columns 
    # (like 'Số tầng', 'Mặt tiền', 'Đường vào'), we will simulate exactly what each approach does.
    
    # Notebook Approach (Approach A)
    df_A = df.copy()
    df_A['Khoảng giá'] = pd.to_numeric(df_A['Khoảng giá'], errors='coerce')
    df_A['Diện tích'] = pd.to_numeric(df_A['Diện tích'], errors='coerce')
    df_A = df_A.dropna(subset=['Khoảng giá', 'Diện tích'])
    df_A = df_A[df_A['Khoảng giá'] >= 1e8]
    # No numeric coercion for 'Số tầng', 'Mặt tiền', 'Đường vào' BEFORE groupby
    
    # Python Script Approach (Approach B)
    df_B = df.copy()
    for col in ['Khoảng giá', 'Diện tích', 'Số tầng', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Mặt tiền', 'Đường vào', 'Tọa độ x', 'Tọa độ y']:
        df_B[col] = pd.to_numeric(df_B[col], errors='coerce')
    df_B = df_B.dropna(subset=['Khoảng giá', 'Diện tích'])
    df_B = df_B[df_B['Khoảng giá'] >= 1e8]
    
    group_cols = [
        'Loại quảng cáo', 'Loại BĐS', 'Tỉnh thành phố', 'Quận', 'Địa chỉ 1', 'Căn góc',
        'Diện tích', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Tên dự án',
        'Hướng nhà', 'Hướng ban công', 'Số tầng', 'Mặt tiền', 'Đường vào',
    ]
    
    # Groupby A (Notebook)
    df_A_grouped = df_A.groupby(group_cols, dropna=False).size().reset_index(name='count')
    
    # Groupby B (Python Script)
    df_B_grouped = df_B.groupby(group_cols, dropna=False).size().reset_index(name='count')
    
    print(f"--- KẾT QUẢ SO SÁNH ---")
    print(f"Tổng số dòng ban đầu trước khi Groupby (sau khi lọc Giá & Diện tích):")
    print(f"  - Approach A (Notebook): {len(df_A)} rows")
    print(f"  - Approach B (Python):   {len(df_B)} rows")
    
    print(f"\nTổng số dòng sau khi Groupby:")
    print(f"  - Approach A (Notebook, không ép kiểu): {len(df_A_grouped)} groups")
    print(f"  - Approach B (Python, ép kiểu numeric): {len(df_B_grouped)} groups")
    
    print(f"\nChênh lệch số nhóm: {len(df_A_grouped) - len(df_B_grouped)}")
    
    print(f"\n--- TÌM VÍ DỤ MINH HỌA ---")
    # Find examples in Approach A where 'Số tầng' is numeric string vs string with characters
    # Look at the raw string values of 'Số tầng' that exist in df_A
    print("Một số giá trị thô của 'Số tầng' trong dữ liệu Notebook trước khi gộp:")
    counts = df_A['Số tầng'].value_counts()
    print(counts.head(10).to_string())
    print("\nCác giá trị thô có chứa chữ cái hoặc ký tự đặc biệt:")
    str_values = counts.index[counts.index.astype(str).str.contains(r'[a-zA-Z\s]', regex=True)]
    for val in str_values[:5]:
        print(f" - '{val}' (xuất hiện {counts[val]} lần)")
        
    print("\nNhờ để nguyên các giá trị chuỗi này, Approach A coi chúng là các nhóm riêng.")
    print("Trong khi đó, Approach B ép kiểu `to_numeric(errors='coerce')` sẽ biến các chuỗi này thành NaN, và gom chung chúng lại với nhau!")

if __name__ == "__main__":
    debug_groupby()
