import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

def export_complete_test():
    print("Loading data for complete export...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    # Cleaning (identical to training to ensure we get the EXACT same rows)
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
    
    # Split using same seed 42
    train_idx, test_idx = train_test_split(df.index, test_size=0.15, random_state=42)
    test_df = df.loc[test_idx]
    
    # Keep ALL original columns to ensure no information is missing
    # But ensure we have the Ad ID column clearly
    test_df.to_csv('complete_test_dataset.csv', index=False, encoding='utf-8-sig')
    print(f"Exported {len(test_df)} complete test samples to 'complete_test_dataset.csv'")

if __name__ == "__main__":
    export_complete_test()
