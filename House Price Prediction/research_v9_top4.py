"""
Research V9: Top 4 Categories + Median-based Dedup + Ensemble.
Focusing on the 4 most popular property types in Hanoi.
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
CENTER_LAT, CENTER_LON = 21.0285, 105.8542

def get_dist_to_metro(px, py):
    return min([np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS])

def load_and_clean_v9():
    print("Loading data and applying V9 Strategy (Top 4 + Median Dedup)...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    # 1. Lọc 'Bán' và 4 loại hình chính
    top_4_types = ['căn hộ chung cư', 'nhà riêng', 'đất', 'nhà mặt phố']
    df = df[(df['Loại quảng cáo'] == 'Bán') & (df['Loại BĐS'].isin(top_4_types))]
    
    for col in ['Khoảng giá', 'Diện tích', 'Số tầng', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Mặt tiền', 'Đường vào', 'Tọa độ x', 'Tọa độ y']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df[df['Khoảng giá'] > 1e8].dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    
    # 2. Khử trùng lặp dùng MEDIAN để chống nhiễu
    group_cols_dedup = [ 
        'Loại quảng cáo', 'Loại BĐS', 'Tỉnh thành phố', 'Quận', 'Phường Xã Thị trấn',
        'Diện tích', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Số tầng', 'Mặt tiền', 'Đường vào'
    ]
    
    df_dedup = df.groupby(group_cols_dedup, dropna=False).agg(
        median_unique_price = ('Khoảng giá', lambda s: np.median(np.unique(s[s.notna()])) if len(np.unique(s[s.notna()]))>0 else np.nan),
        Dia_chi_2=("Địa chỉ 2", "first"),
        Tieu_de=("Tiêu đề", "first"),
        Mo_ta=("Mô tả", "first"),
        Toa_do_x=("Tọa độ x", "first"),
        Toa_do_y=("Tọa độ y", "first")
    ).reset_index().rename(columns={'median_unique_price': 'Price', 'Mo_ta': 'Mô tả', 'Tieu_de': 'Tiêu đề', 'Toa_do_x': 'Tọa độ x', 'Toa_do_y': 'Tọa độ y'})
    
    # 3. Lọc bỏ 1% hàng top theo (Loại BĐS, Quận)
    idx_to_drop = []
    for _, g in df_dedup.groupby(['Loại BĐS', 'Quận']):
        k = max(1, int(np.ceil(len(g) * 0.01)))
        idx_to_drop.extend(g.nlargest(k, 'Price').index.tolist())
    
    df_final = df_dedup.drop(index=idx_to_drop).reset_index(drop=True)
    print(f"Final rows after V9 logic: {len(df_final)}")
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
    df = load_and_clean_v9()
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
    study_xgb.optimize(objective_xgb, n_trials=30)
    
    print("\nPhase 2: Optuna tuning LightGBM...")
    def objective_lgb(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 2000, 4000),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.03),
            'num_leaves': trial.suggest_int('num_leaves', 127, 511),
            'verbose': -1
        }
        m = lgb.LGBMRegressor(**params)
        m.fit(X_train_enc, y_train)
        pred = np.expm1(m.predict(X_test_enc))
        return mean_absolute_percentage_error(np.expm1(y_test), pred)
    
    study_lgb = optuna.create_study(direction='minimize')
    study_lgb.optimize(objective_lgb, n_trials=30)
    
    print("\nPhase 3: Final training and Ensemble...")
    m_xgb = xgb.XGBRegressor(**study_xgb.best_params)
    m_xgb.fit(X_train_enc, y_train)
    m_lgb = lgb.LGBMRegressor(**study_lgb.best_params)
    m_lgb.fit(X_train_enc, y_train)
    
    p_xgb = np.expm1(m_xgb.predict(X_test_enc))
    p_lgb = np.expm1(m_lgb.predict(X_test_enc))
    y_true = np.expm1(y_test)
    
    best_w, best_mape = 0.5, 999
    for w in np.arange(0.0, 1.01, 0.05):
        p = w * p_xgb + (1 - w) * p_lgb
        m = mean_absolute_percentage_error(y_true, p)
        if m < best_mape:
            best_mape, best_w = m, w
    
    print(f"\nFINAL V9 MAPE: {best_mape*100:.2f}% (XGB Weight: {best_w:.2f})")
    
    joblib.dump(m_xgb, 'master_xgb_v9.joblib')
    joblib.dump(m_lgb, 'master_lgb_v9.joblib')
    joblib.dump(encoder, 'master_encoder_v9.joblib')
    joblib.dump(kmeans, 'master_kmeans_v9.joblib')
    print("Models V9 saved.")
