"""
Research V10: Flexible Deduplication (Title-based) + Top 1% Drop.
Aims to keep more data variance while removing extreme outliers.
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
optuna.logging.set_verbosity(optuna.logging.INFO) # Hiện log từng trial để theo dõi progress

METRO_STATIONS = [(21.028, 105.828), (21.015, 105.820), (21.015, 105.810), (21.030, 105.800), (21.002, 105.815), (20.975, 105.776)]
CENTER_LAT, CENTER_LON = 21.0285, 105.8542

def get_dist_to_metro(px, py):
    return min([np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS])

def load_and_clean_v10():
    print("Loading data and applying V10 Strategy (Flexible Dedup)...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    top_4_types = ['căn hộ chung cư', 'nhà riêng', 'đất', 'nhà mặt phố']
    df = df[(df['Loại quảng cáo'] == 'Bán') & (df['Loại BĐS'].isin(top_4_types))]
    
    for col in ['Khoảng giá', 'Diện tích', 'Số tầng', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Mặt tiền', 'Đường vào', 'Tọa độ x', 'Tọa độ y']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df[df['Khoảng giá'] > 1e8].dropna(subset=['Khoảng giá', 'Diện tích'])
    
    # Deduplication theo đúng yêu cầu (15 cột cấu trúc + mean of unique prices)
    group_cols = [
        'Loại quảng cáo', 'Loại BĐS', 'Tỉnh thành phố', 'Quận', 'Địa chỉ 1', 'Căn góc',
        'Diện tích', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Tên dự án',
        'Hướng nhà', 'Hướng ban công', 'Số tầng', 'Mặt tiền', 'Đường vào',
    ]
    
    df_dedup = (
        df.groupby(group_cols, dropna=False)
        .agg(
            mean_unique_khoang_gia=('Khoảng giá', lambda s: np.mean(np.unique(s[s.notna()])) if len(np.unique(s[s.notna()])) > 0 else np.nan),
            phap_ly=('Pháp lý', 'first'),
            noi_that=('Nội thất', 'first'),
            dia_chi_2=('Địa chỉ 2', 'first'),
            tieu_de=('Tiêu đề', 'first'),
            Mo_ta=('Mô tả', 'first'),
            Phuong=('Phường Xã Thị trấn', 'first'),
            Toa_do_x=('Tọa độ x', 'first'),
            Toa_do_y=('Tọa độ y', 'first'),
        )
        .reset_index()
        .rename(columns={
            'mean_unique_khoang_gia': 'Price',
            'Mo_ta': 'Mô tả', 'Phuong': 'Phường Xã Thị trấn',
            'Toa_do_x': 'Tọa độ x', 'Toa_do_y': 'Tọa độ y',
            'dia_chi_2': 'Địa chỉ 2', 'tieu_de': 'Tiêu đề',
            'phap_ly': 'Pháp lý', 'noi_that': 'Nội thất'
        })
    )
    df_dedup = df_dedup.dropna(subset=['Price'])
    print(f"Rows after Deduplication: {len(df_dedup)}")
    
    # Top 1% Drop per (Type, District)
    idx_to_drop = []
    for _, g in df_dedup.groupby(['Loại BĐS', 'Quận']):
        k = max(1, int(np.ceil(len(g) * 0.01)))
        idx_to_drop.extend(g.nlargest(k, 'Price').index.tolist())
    
    df_final = df_dedup.drop(index=idx_to_drop).reset_index(drop=True)
    print(f"Final rows after Top 1% Drop: {len(df_final)}")
    return df_final

def extract_features(df):
    print("Extracting features...")
    df['clean_desc'] = df['Mô tả'].astype(str).apply(text_normalize).str.lower()
    desc = df['clean_desc']
    
    # NLP Features
    df['feat_oto'] = desc.str.contains('xe hơi|ô tô|oto').astype(int)
    df['feat_tranh'] = desc.str.contains('tránh').astype(int)
    df['feat_no_hau'] = desc.str.contains('nở hậu').astype(int)
    df['feat_thang_may'] = desc.str.contains('thang máy').astype(int)
    df['feat_kinh_doanh'] = desc.str.contains('kinh doanh|buôn bán').astype(int)
    df['feat_mat_tien'] = desc.str.contains('mặt phố|mặt đường').astype(int)
    df['feat_noi_that'] = desc.str.contains('nội thất|đầy đủ|tiện nghi').astype(int)
    df['feat_so_do'] = desc.str.contains('sổ đỏ|sổ hồng').astype(int)
    df['feat_chinh_chu'] = desc.str.contains('chính chủ').astype(int)
    
    # Extended NLP Features
    df['feat_view_nui'] = desc.str.contains('view núi|view đồi').astype(int)
    df['feat_view_ho_song'] = desc.str.contains('view hồ|view sông|sát hồ|ven hồ').astype(int)
    df['feat_view_canh_dong'] = desc.str.contains('view cánh đồng|cánh đồng').astype(int)
    df['feat_khuon_vien'] = desc.str.contains('sẵn ao|vườn cây|cây ăn trái|nhà vườn').astype(int)
    df['feat_nghi_duong'] = desc.str.contains('nghỉ dưỡng|homestay|farmstay|villa').astype(int)
    df['feat_nha_xuong'] = desc.str.contains('nhà xưởng').astype(int)
    df['feat_phan_lo'] = desc.str.contains('phân lô').astype(int)
    df['feat_f0'] = desc.str.contains('f0|chưa qua đầu tư').astype(int)
    df['feat_san_nha'] = desc.str.contains('sẵn nhà|nhà cấp 4|ở ngay').astype(int)
    df['feat_duong_nhua'] = desc.str.contains('đường nhựa').astype(int)
    df['feat_duong_betong'] = desc.str.contains('đường bê tông').astype(int)
    df['feat_truc_chinh'] = desc.str.contains('trục chính|đường tỉnh|tỉnh lộ|quốc lộ|đường lớn').astype(int)
    df['feat_phap_ly_chuan'] = desc.str.contains('sẵn sổ|sang tên luôn|pháp lý chuẩn').astype(int)
    df['feat_du_lich'] = desc.str.contains('khu du lịch|resort').astype(int)
    df['feat_truong_hoc'] = desc.str.contains('trường học').astype(int)
    df['feat_cho'] = desc.str.contains('chợ').astype(int)
    df['feat_nga_ba_tu'] = desc.str.contains('ngã 3|ngã 4|ngã tư').astype(int)
    
    df['dist_to_metro'] = df.apply(lambda r: get_dist_to_metro(r['Tọa độ x'], r['Tọa độ y']), axis=1)
    df['dist_to_center'] = np.sqrt((df['Tọa độ x'] - CENTER_LAT)**2 + (df['Tọa độ y'] - CENTER_LON)**2)
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    
    # Số phòng tắm dùng từ group_cols, cần rename về tên chuẩn nếu chưa có
    for col in ['Số tầng', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Mặt tiền', 'Đường vào']:
        df[col] = df[col].astype(str).str.extract(r'(\d+\.?\d*)')[0]
        df[col] = pd.to_numeric(df[col], errors='coerce')    
    # Căn góc: binary 1/0
    df['can_goc'] = (df['Căn góc'].astype(str).str.lower().isin(['có', 'yes', '1', 'true', 'căn góc'])).astype(int)
    
    df['dien_tich_per_tang'] = df['Diện tích'] / df['Số tầng'].replace(0, 1)
    df['mat_tien_x_tang'] = df['Mặt tiền'] * df['Số tầng']
    return df

ALL_FEATURES = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Địa chỉ 1', 'Diện tích', 'Tọa độ x', 'Tọa độ y',
                'Số tầng', 'Số phòng ngủ', 'Số phòng tắm - vệ sinh', 'Mặt tiền', 'Đường vào',
                'Hướng nhà', 'Hướng ban công', 'Pháp lý', 'Nội thất',
                'can_goc',
                'feat_kinh_doanh', 'feat_mat_tien', 'dist_to_metro', 'dist_to_center',
                'type_dist', 'loc_cluster',
                'feat_oto', 'feat_tranh', 'feat_no_hau', 'feat_thang_may',
                'feat_noi_that', 'feat_so_do', 'feat_chinh_chu',
                'feat_view_nui', 'feat_view_ho_song', 'feat_view_canh_dong', 'feat_khuon_vien',
                'feat_nghi_duong', 'feat_nha_xuong', 'feat_phan_lo', 'feat_f0', 'feat_san_nha',
                'feat_duong_nhua', 'feat_duong_betong', 'feat_truc_chinh', 'feat_phap_ly_chuan',
                'feat_du_lich', 'feat_truong_hoc', 'feat_cho', 'feat_nga_ba_tu',
                'dien_tich_per_tang', 'mat_tien_x_tang']
CATEGORICAL = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Địa chỉ 1', 'Hướng nhà', 'Hướng ban công', 'Pháp lý', 'Nội thất', 'type_dist', 'loc_cluster']

if __name__ == "__main__":
    df = load_and_clean_v10()
    df = extract_features(df)
    
    kmeans = MiniBatchKMeans(n_clusters=400, random_state=42, n_init=3)
    coords = df[['Tọa độ x', 'Tọa độ y']].copy()
    coords['Tọa độ x'] = coords['Tọa độ x'].fillna(coords['Tọa độ x'].median())
    coords['Tọa độ y'] = coords['Tọa độ y'].fillna(coords['Tọa độ y'].median())
    df['loc_cluster'] = kmeans.fit_predict(coords)
    
    X = df[ALL_FEATURES]
    y = np.log1p(df['Price'])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
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
            'tree_method': 'hist'  # XGBoost: CPU (AMD GPU không hỗ trợ CUDA)
        }
        m = xgb.XGBRegressor(**params)
        m.fit(X_train_enc, y_train)
        pred = np.expm1(m.predict(X_test_enc))
        return mean_absolute_percentage_error(np.expm1(y_test), pred)
    
    study_xgb = optuna.create_study(direction='minimize')
    study_xgb.optimize(objective_xgb, n_trials=20, show_progress_bar=True)
    
    print("\nPhase 2: Optuna tuning LightGBM...")
    def objective_lgb(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 2000, 5000),
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.03),
            'num_leaves': trial.suggest_int('num_leaves', 255, 1023),
            'device': 'gpu',  # LightGBM: GPU AMD qua OpenCL
            'verbose': -1
        }
        m = lgb.LGBMRegressor(**params)
        m.fit(X_train_enc, y_train)
        pred = np.expm1(m.predict(X_test_enc))
        return mean_absolute_percentage_error(np.expm1(y_test), pred)
    
    study_lgb = optuna.create_study(direction='minimize')
    study_lgb.optimize(objective_lgb, n_trials=20, show_progress_bar=True)
    
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
    
    print(f"\nFINAL V10 MAPE: {best_mape*100:.2f}% (XGB Weight: {best_w:.2f})")
    
    joblib.dump(m_xgb, 'master_xgb_v10.joblib')
    joblib.dump(m_lgb, 'master_lgb_v10.joblib')
    joblib.dump(encoder, 'master_encoder_v10.joblib')
    joblib.dump(kmeans, 'master_kmeans_v10.joblib')
    print("Models V10 saved.")
    
    # --- Test trên HaNoiXtestData & HaNoiYtestData ---
    print("\n--- Testing on HaNoiData (External) ---")
    try:
        X_ext = pd.read_csv('HaNoiXtestData.csv', encoding='utf-8')
        y_ext = pd.read_csv('HaNoiYtestData.csv')
        
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
        
        # Ensure all required columns exist
        for c in ['Địa chỉ 1', 'Căn góc', 'Hướng nhà', 'Hướng ban công', 'Pháp lý', 'Nội thất', 
                  'Số phòng tắm - vệ sinh', 'Phường Xã Thị trấn']:
            if c not in X_ext.columns:
                X_ext[c] = np.nan
        
        for col in ['Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Mặt tiền', 'Đường vào', 'Số phòng ngủ']:
            X_ext[col] = pd.to_numeric(X_ext[col], errors='coerce').fillna(0)
        
        X_ext = extract_features(X_ext.copy())
        X_ext['loc_cluster'] = kmeans.predict(X_ext[['Tọa độ x', 'Tọa độ y']].fillna(X_ext[['Tọa độ x', 'Tọa độ y']].median()))
        
        X_ext_enc = encoder.transform(X_ext[ALL_FEATURES])
        p_xgb_ext = np.expm1(m_xgb.predict(X_ext_enc))
        p_lgb_ext = np.expm1(m_lgb.predict(X_ext_enc))
        y_pred_ext = best_w * p_xgb_ext + (1 - best_w) * p_lgb_ext
        
        y_true_ext = y_ext['mean_unique_khoang_gia_million'] * 1e6
        mape_ext = mean_absolute_percentage_error(y_true_ext, y_pred_ext)
        print(f"MAPE on HaNoiData (External): {mape_ext*100:.2f}%")
    except Exception as e:
        print(f"External test failed: {e}")
