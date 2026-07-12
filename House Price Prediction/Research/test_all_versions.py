import pandas as pd
import numpy as np
import joblib
import importlib
import warnings
from sklearn.metrics import mean_absolute_percentage_error

warnings.filterwarnings('ignore')

VERSIONS = {
    'V6': 'research_v6_optuna',
    'V7': 'research_v7_dedup',
    'V8': 'research_v8_top1',
    'V9': 'research_v9_top4',
    'V10': 'research_v10_flexible'
}


def load_test_data():
    X_ext = pd.read_csv('HaNoiXtestData.csv', encoding='utf-8')
    y_ext = pd.read_csv('HaNoiYtestData.csv')
    
    # Chuẩn hóa tên cột bị lỗi font
    col_idx = X_ext.columns.tolist()
    rename_map = {}
    if len(col_idx) > 1:
        rename_map[col_idx[1]] = 'Loại BĐS'
    if len(col_idx) > 3:
        rename_map[col_idx[3]] = 'Quận'
    if len(col_idx) > 6:
        rename_map[col_idx[6]] = 'Diện tích'
    if len(col_idx) > 7:
        rename_map[col_idx[7]] = 'Số phòng ngủ'
    
    X_ext = X_ext.rename(columns={
        **rename_map,
        'Phuong': 'Phường Xã Thị trấn', 'dia_chi_2': 'Địa chỉ 2',
        'Mo_ta': 'Mô tả', 'Toa_do_x': 'Tọa độ x', 'Toa_do_y': 'Tọa độ y',
        'so_tang': 'Số tầng', 'mat_tien': 'Mặt tiền', 'duong_vao': 'Đường vào'
    })
    
    # Fill các cột mới ở các phiên bản sau nếu chưa có
    for c in ['Địa chỉ 1', 'Căn góc', 'Hướng nhà', 'Hướng ban công', 'Pháp lý', 'Nội thất',
              'Số phòng tắm - vệ sinh', 'Phường Xã Thị trấn']:
        if c not in X_ext.columns:
            X_ext[c] = np.nan
            
    # Ép kiểu dữ liệu số để tránh lỗi string
    for col in ['Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Mặt tiền', 'Đường vào', 'Số phòng ngủ']:
        X_ext[col] = pd.to_numeric(X_ext[col], errors='coerce').fillna(0)
        
    return X_ext, y_ext['mean_unique_khoang_gia_million'] * 1e6


def test_all_versions():
    print("=" * 50)
    print("TESTING ALL VERSIONS ON HANOIDATA")
    print("=" * 50)
    
    X_raw, y_true = load_test_data()
    results = {}
    
    for ver, module_name in VERSIONS.items():
        print(f"\n--- Testing {ver} ---")
        try:
            # 1. Import dynamic
            mod = importlib.import_module(module_name)
            extract_features = getattr(mod, 'extract_features')
            ALL_FEATURES = getattr(mod, 'ALL_FEATURES')
            
            # 2. Load Models
            v_num = ver.lower()
            try:
                m_xgb = joblib.load(f'master_xgb_{v_num}.joblib')
            except FileNotFoundError:
                print(f"Skipping {ver}: Missing XGBoost model.")
                continue
                
            m_lgb = None
            try:
                m_lgb = joblib.load(f'master_lgb_{v_num}.joblib')
            except FileNotFoundError:
                pass  # Bỏ qua nếu không có model LGB
                
            encoder = joblib.load(f'master_encoder_{v_num}.joblib')
            kmeans = joblib.load(f'master_kmeans_{v_num}.joblib')
            
            # 3. Process Data
            X_ext = extract_features(X_raw.copy())
            X_ext['loc_cluster'] = kmeans.predict(X_ext[['Tọa độ x', 'Tọa độ y']].fillna(0))
            
            # Ensure order and encode
            X_ext_features = X_ext[ALL_FEATURES]
            X_ext_enc = encoder.transform(X_ext_features)
            
            # 4. Predict
            p_xgb = np.expm1(m_xgb.predict(X_ext_enc))
            if m_lgb:
                p_lgb = np.expm1(m_lgb.predict(X_ext_enc))
                # Giả định trọng số tốt nhất là 0.70 cho XGB, 0.30 cho LGB
                w = 0.70 if ver in ['V6', 'V7', 'V9'] else 0.65
                y_pred = w * p_xgb + (1 - w) * p_lgb
            else:
                y_pred = p_xgb
                
            mape = mean_absolute_percentage_error(y_true, y_pred) * 100
            print(f"✅ {ver} MAPE: {mape:.2f}%")
            results[ver] = mape
            
        except Exception as e:
            print(f"❌ Error testing {ver}: {e}")
            
    print("\n" + "=" * 50)
    print("FINAL SUMMARY (MAPE on HaNoiData):")
    print("=" * 50)
    for ver, mape in sorted(results.items(), key=lambda x: x[1]):
        print(f"{ver}: {mape:.2f}%")


if __name__ == "__main__":
    test_all_versions()
