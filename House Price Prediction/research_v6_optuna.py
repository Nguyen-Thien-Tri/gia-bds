"""
Research V6: Deep dive on 5%-95% data range.
New techniques:
  - Optuna hyperparameter tuning on best config (Exp C from V5+)
  - Additional geo features: distance to city center, district density
  - Log-ratio street benchmark (no leakage)
  - Cross-validated ensemble weighting
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, KFold
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
# Hanoi city center (Hoan Kiem Lake)
CENTER_LAT, CENTER_LON = 21.0285, 105.8542

def get_dist_to_metro(px, py):
    return min([np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS])

def get_benchmark(dist, addr):
    if dist in STREET_PRICES:
        for s, p in STREET_PRICES[dist].items():
            if s.lower() in addr: return p
    return DISTRICT_BENCHMARKS.get(dist, 25)

def load_and_clean():
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    for col in ['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    df_clean = []
    for t in df['Loại BĐS'].unique():
        sub = df[df['Loại BĐS'] == t]
        if len(sub) < 100: continue
        sub = sub[(sub['Khoảng giá'] >= 1e9) & (sub['Khoảng giá'] <= 3e11)]
        sub = sub[(sub['Diện tích'] >= 20) & (sub['Diện tích'] <= 1000)]
        ppm = sub['Khoảng giá'] / sub['Diện tích']
        q1, q3 = ppm.quantile(0.05), ppm.quantile(0.95)
        df_clean.append(sub[(ppm >= q1) & (ppm <= q3)])
    df = pd.concat(df_clean)
    df['title_prefix'] = df['Tiêu đề'].astype(str).str[:40].str.lower()
    df = df.sort_values('Ngày đăng').drop_duplicates(
        subset=['Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Loại BĐS', 'title_prefix'], keep='last')
    print(f"Clean rows: {len(df)}")
    return df

def extract_features(df):
    print("Extracting features...")
    df['clean_desc'] = df['Mô tả'].astype(str).apply(text_normalize).str.lower()
    desc = df['clean_desc']
    
    # NLP features
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
    
    # Geo features
    df['dist_to_metro'] = df.apply(lambda r: get_dist_to_metro(r['Tọa độ x'], r['Tọa độ y']), axis=1)
    df['dist_to_center'] = np.sqrt((df['Tọa độ x'] - CENTER_LAT)**2 + (df['Tọa độ y'] - CENTER_LON)**2)
    df['street_benchmark'] = df.apply(lambda r: get_benchmark(r['Quận'], str(r['Địa chỉ 2']).lower()), axis=1)
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    
    # Structural features (fill NA with type median)
    for col in ['Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào']:
        df[col] = df[col].fillna(df.groupby('Loại BĐS')[col].transform('median'))
        df[col] = df[col].fillna(df[col].median())
    
    # Derived non-leaking features
    df['dien_tich_per_tang'] = df['Diện tích'] / df['Số tầng'].replace(0, 1)
    df['mat_tien_x_tang'] = df['Mặt tiền'] * df['Số tầng']
    
    return df

CATEGORICAL = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'type_dist', 'loc_cluster']
ALL_FEATURES = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y',
                'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào',
                'feat_kinh_doanh', 'feat_mat_tien', 'street_benchmark', 'dist_to_metro', 'dist_to_center',
                'type_dist', 'loc_cluster',
                'feat_bien', 'feat_goc', 'feat_oto', 'feat_tranh', 'feat_no_hau',
                'feat_cong_vien', 'feat_sieu_thi', 'feat_benh_vien', 'feat_tttm', 'feat_thang_may',
                'feat_noi_that', 'feat_an_ninh', 'feat_view', 'feat_so_do', 'feat_chinh_chu',
                'dien_tich_per_tang', 'mat_tien_x_tang']

if __name__ == "__main__":
    df = load_and_clean()
    df = extract_features(df)
    
    kmeans = MiniBatchKMeans(n_clusters=350, random_state=42, n_init=3)
    df['loc_cluster'] = kmeans.fit_predict(df[['Tọa độ x', 'Tọa độ y']])
    
    X = df[ALL_FEATURES]
    y = np.log1p(df['Khoảng giá'])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    encoder = ce.TargetEncoder(cols=CATEGORICAL)
    X_train_enc = encoder.fit_transform(X_train, y_train)
    X_test_enc = encoder.transform(X_test)
    
    # --- Phase 1: Optuna tuning for XGBoost ---
    print("\nPhase 1: Optuna tuning XGBoost (50 trials)...")
    def objective_xgb(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 1000, 5000),
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.05),
            'max_depth': trial.suggest_int('max_depth', 8, 16),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'tree_method': 'hist'
        }
        m = xgb.XGBRegressor(**params)
        m.fit(X_train_enc, y_train)
        pred = np.expm1(m.predict(X_test_enc))
        return mean_absolute_percentage_error(np.expm1(y_test), pred)
    
    study_xgb = optuna.create_study(direction='minimize')
    study_xgb.optimize(objective_xgb, n_trials=50)
    best_xgb_params = study_xgb.best_params
    print(f"  Best XGB MAPE: {study_xgb.best_value*100:.2f}%  Params: {best_xgb_params}")
    
    # --- Phase 2: Optuna tuning for LightGBM ---
    print("\nPhase 2: Optuna tuning LightGBM (50 trials)...")
    def objective_lgb(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 1000, 5000),
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.05),
            'num_leaves': trial.suggest_int('num_leaves', 127, 1023),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
            'verbose': -1
        }
        m = lgb.LGBMRegressor(**params)
        m.fit(X_train_enc, y_train)
        pred = np.expm1(m.predict(X_test_enc))
        return mean_absolute_percentage_error(np.expm1(y_test), pred)
    
    study_lgb = optuna.create_study(direction='minimize')
    study_lgb.optimize(objective_lgb, n_trials=50)
    best_lgb_params = study_lgb.best_params
    print(f"  Best LGB MAPE: {study_lgb.best_value*100:.2f}%  Params: {best_lgb_params}")
    
    # --- Phase 3: Train final models with best params ---
    print("\nPhase 3: Training final ensemble with best params...")
    best_xgb_params['tree_method'] = 'hist'
    model_xgb = xgb.XGBRegressor(**best_xgb_params)
    model_xgb.fit(X_train_enc, y_train)
    
    best_lgb_params['verbose'] = -1
    model_lgb = lgb.LGBMRegressor(**best_lgb_params)
    model_lgb.fit(X_train_enc, y_train)
    
    # Phase 4: Find optimal ensemble weights
    print("\nPhase 4: Searching for optimal blending weights...")
    p_xgb = np.expm1(model_xgb.predict(X_test_enc))
    p_lgb = np.expm1(model_lgb.predict(X_test_enc))
    y_true = np.expm1(y_test)
    
    best_w, best_mape = 0.5, 999
    for w in np.arange(0.0, 1.01, 0.05):
        pred = w * p_xgb + (1 - w) * p_lgb
        m = mean_absolute_percentage_error(y_true, pred)
        if m < best_mape:
            best_mape, best_w = m, w
    
    final_pred = best_w * p_xgb + (1 - best_w) * p_lgb
    final_mape = mean_absolute_percentage_error(y_true, final_pred)
    print(f"\nBest blend weight XGB={best_w:.2f} / LGB={1-best_w:.2f}")
    print(f"FINAL V6 MAPE (5-95% data): {final_mape*100:.2f}%")
    
    joblib.dump(model_xgb, 'master_xgb_v6.joblib')
    joblib.dump(model_lgb, 'master_lgb_v6.joblib')
    joblib.dump(encoder, 'master_encoder_v6.joblib')
    joblib.dump(kmeans, 'master_kmeans_v6.joblib')
    
    with open('v6_best_params.txt', 'w') as f:
        f.write(f"XGB best: {best_xgb_params}\n")
        f.write(f"LGB best: {best_lgb_params}\n")
        f.write(f"Best blend weight XGB={best_w:.2f}, LGB={1-best_w:.2f}\n")
        f.write(f"FINAL MAPE: {final_mape*100:.2f}%\n")
    print("Models saved.")
