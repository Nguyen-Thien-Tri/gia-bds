import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

def export_test():
    print("Loading and cleaning data for export...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    # Cleaning (same as train_master)
    for col in ['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Số phòng ngủ']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    
    df_clean = []
    for t in df['Loại BĐS'].unique():
        sub = df[df['Loại BĐS'] == t]
        if len(sub) < 100: continue
        sub = sub[(sub['Khoảng giá'] >= 1e9) & (sub['Khoảng giá'] <= 3e11)]
        sub = sub[(sub['Diện tích'] >= 20) & (sub['Diện tích'] <= 1000)]
        ppm = sub['Khoảng giá'] / sub['Diện tích']
        q1, q3 = ppm.quantile(0.1), ppm.quantile(0.9)
        df_clean.append(sub[(ppm >= q1) & (ppm <= q3)])
    df = pd.concat(df_clean)
    
    df['title_prefix'] = df['Tiêu đề'].astype(str).str[:40].str.lower()
    df = df.sort_values('Ngày đăng').drop_duplicates(
        subset=['Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Loại BĐS', 'title_prefix'], keep='last'
    )
    
    # Split using random_state=42 (same as training)
    train_idx, test_idx = train_test_split(df.index, test_size=0.15, random_state=42)
    test_df = df.loc[test_idx]
    
    # Select important columns including 'Mã tin'
    output_cols = ['MA tin', 'Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Địa chỉ 2', 
                   'Diện tích', 'Khoảng giá', 'Số tầng', 'Số phòng ngủ', 'Tiêu đề']
    
    # Fix the column name for 'Mã tin' since it was garbled in the header check
    # It seems to be the second column
    actual_cols = df.columns.tolist()
    ad_id_col = actual_cols[1] # 'MA tin'
    
    export_df = test_df[[ad_id_col, 'Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Địa chỉ 2', 
                        'Diện tích', 'Khoảng giá', 'Số tầng', 'Số phòng ngủ', 'Tiêu đề']]
    
    # Rename for clarity
    export_df.columns = ['Mã tin', 'Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Địa chỉ', 
                         'Diện tích', 'Giá thực tế', 'Số tầng', 'Số phòng ngủ', 'Tiêu đề']
    
    export_df.to_csv('test_dataset_with_ids.csv', index=False, encoding='utf-8-sig')
    print(f"Exported {len(export_df)} test samples to 'test_dataset_with_ids.csv'")

if __name__ == "__main__":
    export_test()
