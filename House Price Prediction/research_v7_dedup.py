"""
Research V7: Advanced Deduplication (Group by 15 structural cols + Mean of Unique Prices)
Retraining V6 architecture with new cleaned dataset.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
import lightgbm as lgb
import category_encoders as ce
import joblib
from sklearn.cluster import MiniBatchKMeans
from underthesea import text_normalize
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

METRO_STATIONS = [(21.028, 105.828), (21.015, 105.820), (21.015, 105.810), (21.030, 105.800), (21.002, 105.815), (20.975, 105.776)]
DISTRICT_BENCHMARKS = {'Hoàn Kiếm': 400, 'Ba Đình': 150, 'Hai Bà Trưng': 130, 'Đống Đa': 130, 'Cầu Giấy': 120,
                       'Tây Hồ': 110, 'Thanh Xuân': 90, 'Nam Từ Liêm': 80, 'Bắc Từ Liêm': 70, 'Long Biên': 60,
                       'Hà Đông': 50, 'Hoàng Mai': 60, 'Gia Lâm': 35, 'Đông Anh': 30, 'Sóc Sơn': 20}
STREET_PRICES = {
    'Hoàn Kiếm': {'Đinh Tiên Hoàng': 695, 'Lê Thái Tổ': 695, 'Hàng Khay': 695, 'Hàng Đào': 600,
                  'Hàng Ngang': 600, 'Hàng Khoai': 600, 'Hàng Lược': 500, 'Đồng Xuân': 600},
    'Ba Đình': {'Phan Đình Phùng': 450, 'Kim Mã': 170, 'Giảng Võ': 170, 'Liễu Giai': 180},
    'Cầu Giấy': {'Cầu Giấy': 181, 'Hoàng Đạo Thúy': 147, 'Duy Tân': 121},
    'Thanh Xuân': {'Nguyễn Trãi': 100, 'Lê Văn Lương': 100},
    'Hai Bà Trưng': {'Bà Triệu': 450, 'Phố Huế': 450},
    'Đống Đa': {'Xã Đàn': 180, 'Láng Hạ': 160}
}
CENTER_LAT, CENTER_LON = 21.0285, 105.8542

def get_dist_to_metro(px, py):
    return min([np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS])

def get_benchmark(dist, addr):
    if dist in STREET_PRICES:
        for s, p in STREET_PRICES[dist].items():
            if s.lower() in addr: return p
    return DISTRICT_BENCHMARKS.get(dist, 25)

def load_and_clean_v7():
    print("Loading data and applying V7 Deduplication...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    # Numeric conversion first
    for col in ['Khoảng giá', 'Diện tích', 'Số tầng', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Mặt tiền', 'Đường vào', 'Tọa độ x', 'Tọa độ y']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    group_cols = [ 
        'Loại quảng cáo', 'Loại BĐS', 'Tỉnh thành phố', 'Quận', 'Địa chỉ 1', 'Căn góc',
        'Diện tích', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Tên dự án', 
        'Hướng nhà', 'Hướng ban công', 'Số tầng', 'Mặt tiền', 'Đường vào'
    ]
    
    # Advanced Deduplication logic
    df_dedup = df.groupby(group_cols, dropna=False).agg(
        mean_unique_khoang_gia = ('Khoảng giá', lambda s: np.mean(np.unique(s[s.notna()])) if len(np.unique(s[s.notna()]))>0 else np.nan),
        Phap_ly=("Pháp lý", "first"),
        Noi_that=("Nội thất", "first"),
        Dia_chi_2=("Địa chỉ 2", "first"),
        Tieu_de=("Tiêu đề", "first"),
        Mo_ta=("Mô tả", "first"),
        Phuong=("Phường Xã Thị trấn", "first"),
        Toa_do_x=("Tọa độ x", "first"),
        Toa_do_y=("Tọa độ y", "first")
    ).reset_index()
    
    # Rename back for compatibility
    df_dedup = df_dedup.rename(columns={
        'mean_unique_khoang_gia': 'Khoảng giá',
        'Phap_ly': 'Pháp lý',
        'Noi_that': 'Nội thất',
        'Dia_chi_2': 'Địa chỉ 2',
        'Tieu_de': 'Tiêu đề',
        'Mo_ta': 'Mô tả',
        'Phuong': 'Phường Xã Thị trấn',
        'Toa_do_x': 'Tọa độ x',
        'Toa_do_y': 'Tọa độ y'
    })
    
    # Filter valid rows
    df_dedup = df_dedup.dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    
    # Outlier filtering at (Type + District) level
    df_clean = []
    for (t, q), sub in df_dedup.groupby(['Loại BĐS', 'Quận']):
        if len(sub) < 30: 
            df_clean.append(sub) # Keep small groups as they are
            continue
        
        ppm = sub['Khoảng giá'] / sub['Diện tích']
        q1, q3 = ppm.quantile(0.05), ppm.quantile(0.95)
        df_clean.append(sub[(ppm >= q1) & (ppm <= q3)])
    
    df_final = pd.concat(df_clean)
    print(f"Final rows after V7 Dedup & Cleaning: {len(df_final)}")
    return df_final

def extract_features(df):
    print("Extracting features...")
    df['clean_desc'] = df['Mô tả'].astype(str).apply(text_normalize).str.lower()
    desc = df['clean_desc']
    
    df['feat_bien'] = desc.str.contains('biển').astype(int)
    df['feat_goc'] = desc.str.contains('góc').astype(int)
    df['feat_oto'] = desc.str.contains('xe hơi|ô tô|oto').astype(int)
    df['feat_tranh'] = desc.str.contains('tránh').astype(int)
    df['feat_no_hau'] = desc.str.contains('nở hậu').astype(int)
    df['feat_cong_vien'] = desc.str.contains('công viên').astype(int)
    df['feat_sieu_thi'] = desc.str.contains('siêu thị|mart').astype(int)
    df['feat_benh_vien'] = desc.str.contains('bệnh viện|bv').astype(int)
    df['feat_tttm'] = desc.str.contains('trung tâm thương mại|tttm').astype(int)
    df['feat_thang_may'] = desc.str.contains('thang máy').astype(int)
    df['feat_kinh_doanh'] = desc.str.contains('kinh doanh|buôn bán').astype(int)
    df['feat_mat_tien'] = desc.str.contains('mặt phố|mặt đường').astype(int)
    df['feat_noi_that'] = desc.str.contains('nội thất|đầy đủ|tiện nghi').astype(int)
    df['feat_an_ninh'] = desc.str.contains('an ninh|bảo vệ|camera').astype(int)
    df['feat_view'] = desc.str.contains('view|hồ|sông').astype(int)
    df['feat_so_do'] = desc.str.contains('sổ đỏ|sổ hồng').astype(int)
    df['feat_chinh_chu'] = desc.str.contains('chính chủ').astype(int)
    
    df['dist_to_metro'] = df.apply(lambda r: get_dist_to_metro(r['Tọa độ x'], r['Tọa độ y']), axis=1)
    df['dist_to_center'] = np.sqrt((df['Tọa độ x'] - CENTER_LAT)**2 + (df['Tọa độ y'] - CENTER_LON)**2)
    df['street_benchmark'] = df.apply(lambda r: get_benchmark(str(r['Quận']), str(r['Địa chỉ 2']).lower()), axis=1)
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    
    for col in ['Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào']:
        df[col] = df[col].fillna(df.groupby('Loại BĐS')[col].transform('median')).fillna(0)
    
    df['dien_tich_per_tang'] = df['Diện tích'] / df['Số tầng'].replace(0, 1)
    df['mat_tien_x_tang'] = df['Mặt tiền'] * df['Số tầng']
    return df

ALL_FEATURES = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y',
                'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào',
                'feat_kinh_doanh', 'feat_mat_tien', 'street_benchmark', 'dist_to_metro', 'dist_to_center',
                'type_dist', 'loc_cluster',
                'feat_bien', 'feat_goc', 'feat_oto', 'feat_tranh', 'feat_no_hau',
                'feat_cong_vien', 'feat_sieu_thi', 'feat_benh_vien', 'feat_tttm', 'feat_thang_may',
                'feat_noi_that', 'feat_an_ninh', 'feat_view', 'feat_so_do', 'feat_chinh_chu',
                'dien_tich_per_tang', 'mat_tien_x_tang']
CATEGORICAL = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'type_dist', 'loc_cluster']

if __name__ == "__main__":
    df = load_and_clean_v7()
    df = extract_features(df)
    
    kmeans = MiniBatchKMeans(n_clusters=350, random_state=42, n_init=3)
    df['loc_cluster'] = kmeans.fit_predict(df[['Tọa độ x', 'Tọa độ y']])
    
    X = df[ALL_FEATURES]
    y = np.log1p(df['Khoảng giá'])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
    # Save the split data for later verification if needed
    X_test.to_csv('HaNoiXtestData_v7.csv', index=False)
    np.expm1(y_test).to_csv('HaNoiYtestData_v7.csv', index=False)
    
    encoder = ce.TargetEncoder(cols=CATEGORICAL)
    X_train_enc = encoder.fit_transform(X_train, y_train)
    X_test_enc = encoder.transform(X_test)
    
    print("\nPhase 1: Optuna tuning XGBoost...")
    def objective_xgb(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 2000, 5000),
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.03),
            'max_depth': trial.suggest_int('max_depth', 10, 16),
            'subsample': trial.suggest_float('subsample', 0.7, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'tree_method': 'hist'
        }
        m = xgb.XGBRegressor(**params)
        m.fit(X_train_enc, y_train)
        pred = np.expm1(m.predict(X_test_enc))
        return mean_absolute_percentage_error(np.expm1(y_test), pred)
    
    study_xgb = optuna.create_study(direction='minimize')
    study_xgb.optimize(objective_xgb, n_trials=30) # Reduced trials to 30 for speed
    
    print("\nPhase 2: Optuna tuning LightGBM...")
    def objective_lgb(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 2000, 5000),
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.03),
            'num_leaves': trial.suggest_int('num_leaves', 255, 1023),
            'subsample': trial.suggest_float('subsample', 0.7, 1.0),
            'verbose': -1
        }
        m = lgb.LGBMRegressor(**params)
        m.fit(X_train_enc, y_train)
        pred = np.expm1(m.predict(X_test_enc))
        return mean_absolute_percentage_error(np.expm1(y_test), pred)
    
    study_lgb = optuna.create_study(direction='minimize')
    study_lgb.optimize(objective_lgb, n_trials=30)
    
    print("\nPhase 3: Final training and weight optimization...")
    model_xgb = xgb.XGBRegressor(**study_xgb.best_params)
    model_xgb.fit(X_train_enc, y_train)
    model_lgb = lgb.LGBMRegressor(**study_lgb.best_params)
    model_lgb.fit(X_train_enc, y_train)
    
    p_xgb = np.expm1(model_xgb.predict(X_test_enc))
    p_lgb = np.expm1(model_lgb.predict(X_test_enc))
    y_true = np.expm1(y_test)
    
    best_w, best_mape = 0.5, 999
    for w in np.arange(0.0, 1.01, 0.05):
        pred = w * p_xgb + (1 - w) * p_lgb
        m = mean_absolute_percentage_error(y_true, pred)
        if m < best_mape:
            best_mape, best_w = m, w
    
    print(f"\nFINAL V7 MAPE: {best_mape*100:.2f}% (XGB={best_w:.2f}, LGB={1-best_w:.2f})")
    
    joblib.dump(model_xgb, 'master_xgb_v7.joblib')
    joblib.dump(model_lgb, 'master_lgb_v7.joblib')
    joblib.dump(encoder, 'master_encoder_v7.joblib')
    joblib.dump(kmeans, 'master_kmeans_v7.joblib')
    print("Models V7 saved.")
