import pandas as pd
import numpy as np

# 1. Tải dữ liệu thô
df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
for col in ['Khoảng giá', 'Diện tích', 'Số tầng', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Mặt tiền', 'Đường vào', 'Tọa độ x', 'Tọa độ y']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 2. Tìm một tin đăng lỗi giá cực nặng (ví dụ căn 88m2 giá 8.830 tỷ)
error_sample = df[df['Khoảng giá'] > 5e12].head(1)
if error_sample.empty:
    print("No extreme error found above 5e12, searching lower...")
    error_sample = df[df['Khoảng giá'] > 1e12].head(1)

print("--- STEP 1: TIN ĐĂNG GỐC BỊ LỖI ---")
print(error_sample[['Mã tin', 'Quận', 'Loại BĐS', 'Diện tích', 'Khoảng giá', 'Tiêu đề']])

# 3. Mô phỏng quá trình gộp (Deduplication) của V7
group_cols = [ 
    'Loại quảng cáo', 'Loại BĐS', 'Tỉnh thành phố', 'Quận', 'Địa chỉ 1', 'Căn góc',
    'Diện tích', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Tên dự án', 
    'Hướng nhà', 'Hướng ban công', 'Số tầng', 'Mặt tiền', 'Đường vào'
]

# Lấy các giá trị thuộc nhóm của tin lỗi này
mask = True
for col in group_cols:
    val = error_sample[col].iloc[0]
    if pd.isna(val):
        mask &= df[col].isna()
    else:
        mask &= (df[col] == val)

group_members = df[mask]
print(f"\n--- STEP 2: CÁC TIN ĐĂNG CÙNG NHÓM GỘP ({len(group_members)} tin) ---")
print(group_members[['Mã tin', 'Khoảng giá', 'Tiêu đề']])

# Tính mean_unique_khoang_gia như V7
unique_prices = np.unique(group_members['Khoảng giá'].dropna())
mean_price = np.mean(unique_prices)
print(f"\n=> GIÁ SAU KHI GỘP (Mean of Unique): {mean_price:,.0f} VNĐ")

# 4. Kiểm tra bộ lọc Phân vị của Quận + Loại hình đó
target_type = error_sample['Loại BĐS'].iloc[0]
target_dist = error_sample['Quận'].iloc[0]

# Giả lập toàn bộ tập sau gộp để tính Quantile
df_dedup_lite = df.groupby(group_cols, dropna=False)['Khoảng giá'].agg(lambda s: np.mean(np.unique(s[s.notna()])) if len(np.unique(s[s.notna()]))>0 else np.nan).reset_index()
df_dedup_lite = df_dedup_lite.rename(columns={'Khoảng giá': 'Price'})

# Lấy phân phối của Quận + Loại hình mục tiêu
district_type_group = df_dedup_lite[(df_dedup_lite['Loại BĐS'] == target_type) & (df_dedup_lite['Quận'] == target_dist)].copy()
district_type_group['PPM'] = district_type_group['Price'] / district_type_group['Diện tích']

q1 = district_type_group['PPM'].quantile(0.05)
q3 = district_type_group['PPM'].quantile(0.95)

print(f"\n--- STEP 3: PHÂN PHỐI CỦA NHÓM [{target_type} - {target_dist}] ---")
print(f"Số lượng mẫu trong nhóm: {len(district_type_group)}")
print(f"PPM Quantile 5% (q1): {q1:,.0f}")
print(f"PPM Quantile 95% (q3): {q3:,.0f}")

my_ppm = mean_price / error_sample['Diện tích'].iloc[0]
print(f"PPM CỦA TIN LỖI SAU GỘP: {my_ppm:,.0f}")

if my_ppm > q3:
    print("\n=> KẾT QUẢ: Tin này NẰM NGOÀI dải 95%, ĐÁNG LẼ PHẢI BỊ LOẠI.")
else:
    print("\n=> KẾT QUẢ: Tin này LỌT QUA VÌ NẰM TRONG dải 5-95%.")
    print("Lý do: Trong nhóm này có quá nhiều tin lỗi tương tự, làm đẩy mức q3 lên cực cao!")
