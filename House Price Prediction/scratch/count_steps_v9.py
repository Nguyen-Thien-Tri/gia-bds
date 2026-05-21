import pandas as pd
import numpy as np

# Load
df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
print(f"1. Tổng dữ liệu gốc: {len(df):,} dòng")

# Step 2
top_4_types = ['căn hộ chung cư', 'nhà riêng', 'đất', 'nhà mặt phố']
df_ban = df[(df['Loại quảng cáo'] == 'Bán') & (df['Loại BĐS'].isin(top_4_types))].copy()
print(f"2. Sau khi lọc Bán + Top 4 loại hình: {len(df_ban):,} dòng")

# Step 3
for col in ['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y']:
    df_ban[col] = pd.to_numeric(df_ban[col], errors='coerce')
df_valid = df_ban[df_ban['Khoảng giá'] > 1e8].dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
print(f"3. Sau khi lọc giá > 100tr & bỏ NaN: {len(df_valid):,} dòng")

# Step 4
group_cols = [
    'Loại quảng cáo', 'Loại BĐS', 'Tỉnh thành phố', 'Quận', 'Phường Xã Thị trấn',
    'Diện tích', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Số tầng', 'Mặt tiền', 'Đường vào'
]
df_dedup = df_valid.groupby(group_cols, dropna=False).size().reset_index()
print(f"4. Sau khi Khử trùng lặp (Deduplication cấp Phường): {len(df_dedup):,} dòng")

# Step 5
idx_to_drop = []
# Group by dist/type to identify top 1% prices
# First we need the prices in df_dedup
df_dedup_price = df_valid.groupby(group_cols, dropna=False)['Khoảng giá'].median().reset_index()
for _, g in df_dedup_price.groupby(['Loại BĐS', 'Quận']):
    k = max(1, int(np.ceil(len(g) * 0.01)))
    idx_to_drop.extend(g.nlargest(k, 'Khoảng giá').index.tolist())

print(f"5. Sau khi loại bỏ 1% giá cao nhất (Top 1% Drop): {len(df_dedup_price) - len(idx_to_drop):,} dòng")
