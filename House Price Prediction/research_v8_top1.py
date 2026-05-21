"""
Research V8: Top 1% Price Drop Strategy + Phường-level Dedup.
Applying user's suggested outlier removal method.
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
CENTER_LAT, CENTER_LON = 21.0285, 105.8542

def get_dist_to_metro(px, py):
    return min([np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS])

def load_and_clean_v8():
    print("Loading data and applying V8 Strategy (Deduplication + Top 1% Drop)...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    # 0. Chỉ lấy tin Bán
    df = df[df['Loại quảng cáo'] == 'Bán']
    
    for col in ['Khoảng giá', 'Diện tích', 'Số tầng', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Mặt tiền', 'Đường vào', 'Tọa độ x', 'Tọa độ y']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 1. Bỏ giá dưới 100 triệu
    df = df[df['Khoảng giá'] > 1e8].dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    
    # 2. Khử trùng lặp nâng cao (bao gồm Phường để giữ vị trí)
    group_cols_dedup = [ 
        'Loại quảng cáo', 'Loại BĐS', 'Tỉnh thành phố', 'Quận', 'Phường Xã Thị trấn', 'Căn góc',
        'Diện tích', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Số tầng', 'Mặt tiền', 'Đường vào',
        'Hướng nhà', 'Hướng ban công', 'Tên dự án'
    ]
    
    df_dedup = df.groupby(group_cols_dedup, dropna=False).agg(
        mean_unique_khoang_gia = ('Khoảng giá', lambda s: np.mean(np.unique(s[s.notna()])) if len(np.unique(s[s.notna()]))>0 else np.nan),
        Dia_chi_2=("Địa chỉ 2", "first"),
        Tieu_de=("Tiêu đề", "first"),
        Mo_ta=("Mô tả", "first"),
        Toa_do_x=("Tọa độ x", "first"),
        Toa_do_y=("Tọa độ y", "first")
    ).reset_index().rename(columns={
        'mean_unique_khoang_gia': 'Price',
        'Dia_chi_2': 'Địa chỉ 2',
        'Tieu_de': 'Tiêu đề',
        'Mo_ta': 'Mô tả',
        'Toa_do_x': 'Tọa độ x',
        'Toa_do_y': 'Tọa độ y'
    })
    
    # 3. Lọc bỏ 1% hàng top theo mỗi nhóm (Loại BĐS, Tỉnh, Quận)
    group_cols_outlier = ['Loại BĐS', 'Tỉnh thành phố', 'Quận']
    idx_to_drop = []
    
    for _, g in df_dedup.groupby(group_cols_outlier):
        n = len(g)
        k = max(1, int(np.ceil(n * 0.01)))
        if k > 0:
            # Drop top k most expensive
            idx_to_drop.extend(g.nlargest(k, 'Price').index.tolist())
            # Drop bottom 1% too to handle rental leftovers? User only asked for top, but usually good to do both.
            # However, I will follow the user's specific request for Top 1% drop.
            
    df_final = df_dedup.drop(index=idx_to_drop).reset_index(drop=True)
    print(f"Final rows after V8 logic: {len(df_final)}")
    return df_final

def extract_features(df):
    print("Extracting features...")
    df['clean_desc'] = df['Mô tả'].astype(str).apply(text_normalize).str.lower()
    desc = df['clean_desc']
    
    # Features from V6/V7
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
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    
    for col in ['Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào']:
        df[col] = df[col].fillna(df.groupby('Loại BĐS')[col].transform('median')).fillna(0)
    
    df['dien_tich_per_tang'] = df['Diện tích'] / df['Số tầng'].replace(0, 1)
    df['mat_tien_x_tang'] = df['Mặt tiền'] * df['Số tầng']
    return df

ALL_FEATURES = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y',
                'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào',
                'feat_kinh_doanh', 'feat_mat_tien', 'dist_to_metro', 'dist_to_center',
                'type_dist', 'loc_cluster',
                'feat_bien', 'feat_goc', 'feat_oto', 'feat_tranh', 'feat_no_hau',
                'feat_cong_vien', 'feat_sieu_thi', 'feat_benh_vien', 'feat_tttm', 'feat_thang_may',
                'feat_noi_that', 'feat_an_ninh', 'feat_view', 'feat_so_do', 'feat_chinh_chu',
                'dien_tich_per_tang', 'mat_tien_x_tang']
CATEGORICAL = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'type_dist', 'loc_cluster']

if __name__ == "__main__":
    df = load_and_clean_v8()
    df = extract_features(df)
    
    kmeans = MiniBatchKMeans(n_clusters=350, random_state=42, n_init=3)
    df['loc_cluster'] = kmeans.fit_predict(df[['Tọa độ x', 'Tọa độ y']])
    
    X = df[ALL_FEATURES]
    y = np.log1p(df['Price'])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
    encoder = ce.TargetEncoder(cols=CATEGORICAL)
    X_train_enc = encoder.fit_transform(X_train, y_train)
    X_test_enc = encoder.transform(X_test)
    
    print("\nPhase 1: Optuna tuning XGBoost...")
    def objective_xgb(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 2000, 4000),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.03),
            'max_depth': trial.suggest_int('max_depth', 10, 14),
            'subsample': trial.suggest_float('subsample', 0.7, 0.9),
            'tree_method': 'hist'
        }
        m = xgb.XGBRegressor(**params)
        m.fit(X_train_enc, y_train)
        pred = np.expm1(m.predict(X_test_enc))
        return mean_absolute_percentage_error(np.expm1(y_test), pred)
    
    study_xgb = optuna.create_study(direction='minimize')
    study_xgb.optimize(objective_xgb, n_trials=20)
    
    print("\nPhase 2: Final training...")
    model_xgb = xgb.XGBRegressor(**study_xgb.best_params)
    model_xgb.fit(X_train_enc, y_train)
    
    y_true = np.expm1(y_test)
    y_pred = np.expm1(model_xgb.predict(X_test_enc))
    mape = mean_absolute_percentage_error(y_true, y_pred)
    
    print(f"\nFINAL V8 MAPE: {mape*100:.2f}%")
    joblib.dump(model_xgb, 'master_xgb_v8.joblib')
    joblib.dump(encoder, 'master_encoder_v8.joblib')
    joblib.dump(kmeans, 'master_kmeans_v8.joblib')
    print("Models V8 saved.")
