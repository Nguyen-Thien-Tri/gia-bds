import pandas as pd
import numpy as np

def count_rows():
    print('1. Đọc file CSV gốc (filtered_hanoi_data.csv)...')
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    print(f'   -> Số dòng: {len(df):,}')
    
    top_4_types = ['căn hộ chung cư', 'nhà riêng', 'đất', 'nhà mặt phố']
    df = df[(df['Loại quảng cáo'] == 'Bán') & (df['Loại BĐS'].isin(top_4_types))]
    print(f'2. Chỉ lấy tin Bán & Top 4 loại hình BĐS:\n   -> Số dòng: {len(df):,}')
    
    for col in ['Khoảng giá', 'Diện tích', 'Số tầng', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Mặt tiền', 'Đường vào', 'Tọa độ x', 'Tọa độ y']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df = df[df['Khoảng giá'] > 1e8].dropna(subset=['Khoảng giá', 'Diện tích'])
    print(f'3. Bỏ giá < 100tr & dropna (Khoảng giá, Diện tích):\n   -> Số dòng: {len(df):,}')
    
    group_cols = ['Loại quảng cáo', 'Loại BĐS', 'Tỉnh thành phố', 'Quận', 'Địa chỉ 1', 'Căn góc', 'Diện tích', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Tên dự án', 'Hướng nhà', 'Hướng ban công', 'Số tầng', 'Mặt tiền', 'Đường vào']
    df_dedup = df.groupby(group_cols, dropna=False).agg(
        mean_unique_khoang_gia=('Khoảng giá', lambda s: np.mean(np.unique(s[s.notna()])) if len(np.unique(s[s.notna()])) > 0 else np.nan)
    ).reset_index()
    print(f'4. Gộp nhóm khử trùng lặp (15 cột cấu trúc):\n   -> Số dòng: {len(df_dedup):,}')
    
    group_cols_outlier = ['Loại BĐS', 'Tỉnh thành phố', 'Quận']
    idx_to_drop = []
    df_dedup = df_dedup.rename(columns={'mean_unique_khoang_gia': 'Price'})
    
    for _, g in df_dedup.groupby(group_cols_outlier):
        k = max(1, int(np.ceil(len(g) * 0.01)))
        if k > 0:
            idx_to_drop.extend(g.nlargest(k, 'Price').index.tolist())
            
    df_final = df_dedup.drop(index=idx_to_drop).reset_index(drop=True)
    print(f'5. Bỏ 1% giá cao nhất theo từng Quận/Loại hình:\n   -> Số dòng cuối cùng đem đi train: {len(df_final):,}')

if __name__ == "__main__":
    count_rows()
