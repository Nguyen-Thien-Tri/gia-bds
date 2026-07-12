import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_absolute_percentage_error
from research_v10_flexible import extract_features, ALL_FEATURES

def test_v10_hanoi_data():
    print("Loading V10 models...")
    try:
        m_xgb = joblib.load('master_xgb_v10.joblib')
        m_lgb = joblib.load('master_lgb_v10.joblib')
        encoder = joblib.load('master_encoder_v10.joblib')
        kmeans = joblib.load('master_kmeans_v10.joblib')
    except Exception as e:
        print(f"Error loading models: {e}")
        print("Vui lòng đảm bảo các file master_*_v10.joblib đã được tạo.")
        return

    print("Loading test data...")
    try:
        X_ext = pd.read_csv('HaNoiXtestData.csv', encoding='utf-8')
        y_ext = pd.read_csv('HaNoiYtestData.csv')
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("Preprocessing data...")
    # Rename garbled columns to match our pipeline
    col_idx = X_ext.columns.tolist()
    rename_map = {}
    if len(col_idx) > 1: rename_map[col_idx[1]] = 'Loại BĐS'
    if len(col_idx) > 3: rename_map[col_idx[3]] = 'Quận'
    if len(col_idx) > 6: rename_map[col_idx[6]] = 'Diện tích'
    if len(col_idx) > 7: rename_map[col_idx[7]] = 'Số phòng ngủ'
    
    X_ext = X_ext.rename(columns={**rename_map,
        'Phuong': 'Phường Xã Thị trấn', 'dia_chi_2': 'Địa chỉ 2',
        'Mo_ta': 'Mô tả', 'Toa_do_x': 'Tọa độ x', 'Toa_do_y': 'Tọa độ y',
        'so_tang': 'Số tầng', 'mat_tien': 'Mặt tiền', 'duong_vao': 'Đường vào'
    })
    
    # Đảm bảo các cột categorical mới có tồn tại (nếu thiếu thì fill NaN)
    for c in ['Địa chỉ 1', 'Căn góc', 'Hướng nhà', 'Hướng ban công', 'Pháp lý', 'Nội thất', 
              'Số phòng tắm - vệ sinh', 'Phường Xã Thị trấn']:
        if c not in X_ext.columns:
            X_ext[c] = np.nan
            
    # Chuyển đổi kiểu dữ liệu số
    for col in ['Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Mặt tiền', 'Đường vào', 'Số phòng ngủ']:
        X_ext[col] = pd.to_numeric(X_ext[col], errors='coerce').fillna(0)
    
    print("Extracting features...")
    X_ext = extract_features(X_ext.copy())
    
    # Dự đoán loc_cluster (fill NaN tạm bằng 0 nếu thiếu tọa độ)
    X_ext['loc_cluster'] = kmeans.predict(X_ext[['Tọa độ x', 'Tọa độ y']].fillna(0))
    
    # Đảm bảo thứ tự cột chuẩn trước khi encode
    X_ext_features = X_ext[ALL_FEATURES]
    X_ext_enc = encoder.transform(X_ext_features)
    
    print("Predicting...")
    p_xgb_ext = np.expm1(m_xgb.predict(X_ext_enc))
    p_lgb_ext = np.expm1(m_lgb.predict(X_ext_enc))
    
    # Sử dụng trọng số tốt nhất từ quá trình train (mặc định 0.65 cho XGB)
    best_w = 0.65
    y_pred_ext = best_w * p_xgb_ext + (1 - best_w) * p_lgb_ext
    
    # Target thực tế tính bằng triệu đồng
    y_true_ext = y_ext['mean_unique_khoang_gia_million'] * 1e6
    
    mape_ext = mean_absolute_percentage_error(y_true_ext, y_pred_ext)
    print(f"\n==========================================")
    print(f"MAPE V10 on HaNoiData (External): {mape_ext*100:.2f}%")
    print(f"==========================================")

if __name__ == "__main__":
    test_v10_hanoi_data()
