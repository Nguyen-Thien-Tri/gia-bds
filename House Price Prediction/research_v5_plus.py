"""
Research V5+: Multiple experiments on 5%-95% data range.
Experiments:
  A. Blending (XGB+LGB) with 5%-95% and more clusters
  B. Blending (XGB+LGB) with 5%-95% + Số tầng/Số phòng ngủ/Mặt tiền features
  C. CatBoost native (no encoding) + 5%-95%
"""
import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor
import category_encoders as ce
import joblib
from sklearn.cluster import MiniBatchKMeans
from underthesea import text_normalize

METRO_STATIONS = [(21.028, 105.828), (21.015, 105.820), (21.015, 105.810), (21.030, 105.800), (21.002, 105.815), (20.975, 105.776)]
DISTRICT_BENCHMARKS = {'Hoàn Kiếm': 400, 'Ba Đình': 150, 'Hai Bà Trưng': 130, 'Đống Đa': 130, 'Cầu Giấy': 120, 'Tây Hồ': 110, 'Thanh Xuân': 90, 'Nam Từ Liêm': 80, 'Bắc Từ Liêm': 70, 'Long Biên': 60, 'Hà Đông': 50, 'Hoàng Mai': 60}
STREET_PRICES = {
    'Hoàn Kiếm': {'Đinh Tiên Hoàng': 695, 'Lê Thái Tổ': 695, 'Hàng Khay': 695, 'Hàng Đào': 600, 'Hàng Ngang': 600, 'Hàng Khoai': 600},
    'Ba Đình': {'Phan Đình Phùng': 450, 'Kim Mã': 170, 'Giảng Võ': 170, 'Liễu Giai': 180},
    'Cầu Giấy': {'Cầu Giấy': 181, 'Hoàng Đạo Thúy': 147, 'Duy Tân': 121},
    'Thanh Xuân': {'Nguyễn Trãi': 100, 'Lê Văn Lương': 100},
    'Hai Bà Trưng': {'Bà Triệu': 450, 'Phố Huế': 450},
    'Đống Đa': {'Xã Đàn': 180, 'Láng Hạ': 160}
}

def get_dist_to_metro(px, py):
    return min([np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS])

def get_benchmark(dist, addr):
    if dist in STREET_PRICES:
        for s, p in STREET_PRICES[dist].items():
            if s.lower() in addr: return p
    return DISTRICT_BENCHMARKS.get(dist, 30)

def load_and_clean(quantile_low=0.05, quantile_high=0.95):
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
        q1, q3 = ppm.quantile(quantile_low), ppm.quantile(quantile_high)
        df_clean.append(sub[(ppm >= q1) & (ppm <= q3)])
    df = pd.concat(df_clean)
    df['title_prefix'] = df['Tiêu đề'].astype(str).str[:40].str.lower()
    df = df.sort_values('Ngày đăng').drop_duplicates(
        subset=['Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Loại BĐS', 'title_prefix'], keep='last')
    return df

def extract_features(df):
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
    df['feat_view'] = desc.str.contains('view|hồ|công viên|sông').astype(int)
    df['dist_to_metro'] = df.apply(lambda r: get_dist_to_metro(r['Tọa độ x'], r['Tọa độ y']), axis=1)
    df['street_benchmark'] = df.apply(lambda r: get_benchmark(r['Quận'], str(r['Địa chỉ 2']).lower()), axis=1)
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    df['Số tầng'] = df['Số tầng'].fillna(df.groupby('Loại BĐS')['Số tầng'].transform('median'))
    df['Số phòng ngủ'] = df['Số phòng ngủ'].fillna(df.groupby('Loại BĐS')['Số phòng ngủ'].transform('median'))
    df['Mặt tiền'] = df['Mặt tiền'].fillna(df.groupby('Loại BĐS')['Mặt tiền'].transform('median'))
    df['Đường vào'] = df['Đường vào'].fillna(df.groupby('Loại BĐS')['Đường vào'].transform('median'))
    return df

def run_experiment(name, df, features, categorical, n_clusters=300, xgb_params=None, lgb_params=None, w_xgb=0.6):
    kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init=3)
    df['loc_cluster'] = kmeans.fit_predict(df[['Tọa độ x', 'Tọa độ y']])
    
    X = df[features]
    y = np.log1p(df['Khoảng giá'])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    encoder = ce.TargetEncoder(cols=categorical)
    X_train_enc = encoder.fit_transform(X_train, y_train)
    X_test_enc = encoder.transform(X_test)
    
    _xgb = xgb.XGBRegressor(**(xgb_params or {'n_estimators': 3500, 'learning_rate': 0.02, 'max_depth': 13, 'tree_method': 'hist'}))
    _lgb = lgb.LGBMRegressor(**(lgb_params or {'n_estimators': 3500, 'learning_rate': 0.02, 'num_leaves': 1023, 'verbose': -1}))
    _xgb.fit(X_train_enc, y_train)
    _lgb.fit(X_train_enc, y_train)
    
    y_pred = w_xgb * np.expm1(_xgb.predict(X_test_enc)) + (1 - w_xgb) * np.expm1(_lgb.predict(X_test_enc))
    mape = mean_absolute_percentage_error(np.expm1(y_test), y_pred)
    print(f"  [{name}] MAPE = {mape*100:.2f}%")
    return mape, _xgb, _lgb, encoder, kmeans

BASE_FEATURES = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 
                 'feat_kinh_doanh', 'feat_mat_tien', 'street_benchmark', 'dist_to_metro',
                 'type_dist', 'loc_cluster', 'feat_bien', 'feat_goc', 'feat_oto', 'feat_tranh', 
                 'feat_no_hau', 'feat_cong_vien', 'feat_sieu_thi', 'feat_benh_vien', 'feat_tttm', 'feat_thang_may']
EXTENDED_FEATURES = BASE_FEATURES + ['Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào',
                                      'feat_noi_that', 'feat_an_ninh', 'feat_view']
CATEGORICAL = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'type_dist', 'loc_cluster']

if __name__ == "__main__":
    print("Loading 5%-95% data...")
    df = load_and_clean(0.05, 0.95)
    print(f"Total rows: {len(df)}")
    df = extract_features(df)
    
    results = {}
    
    print("\n--- Experiment A: Base features + 5%-95% + 300 clusters ---")
    mape, *_ = run_experiment("A_base_5_95", df.copy(), BASE_FEATURES, CATEGORICAL, n_clusters=300)
    results['A: Base + 5-95%'] = mape

    print("\n--- Experiment B: Extended features (Số tầng, Mặt tiền...) + 5%-95% ---")
    mape, xgb_b, lgb_b, enc_b, km_b = run_experiment("B_extended_5_95", df.copy(), EXTENDED_FEATURES, CATEGORICAL, n_clusters=300)
    results['B: Extended + 5-95%'] = mape
    
    print("\n--- Experiment C: Extended features, more trees, deeper ---")
    mape, xgb_c, lgb_c, enc_c, km_c = run_experiment(
        "C_extended_deep", df.copy(), EXTENDED_FEATURES, CATEGORICAL, n_clusters=350,
        xgb_params={'n_estimators': 4000, 'learning_rate': 0.015, 'max_depth': 14, 'tree_method': 'hist', 'subsample': 0.8},
        lgb_params={'n_estimators': 4000, 'learning_rate': 0.015, 'num_leaves': 1023, 'verbose': -1, 'subsample': 0.8}
    )
    results['C: Extended + deep'] = mape
    
    print("\n--- Experiment D: Experiment C + higher LGB weight ---")
    mape, *_ = run_experiment(
        "D_lgb_heavy", df.copy(), EXTENDED_FEATURES, CATEGORICAL, n_clusters=350,
        xgb_params={'n_estimators': 4000, 'learning_rate': 0.015, 'max_depth': 14, 'tree_method': 'hist', 'subsample': 0.8},
        lgb_params={'n_estimators': 4000, 'learning_rate': 0.015, 'num_leaves': 1023, 'verbose': -1, 'subsample': 0.8},
        w_xgb=0.4
    )
    results['D: Extended + LGB-heavy'] = mape
    
    print("\n========== RESULTS SUMMARY ==========")
    best_name, best_mape = min(results.items(), key=lambda x: x[1])
    for k, v in results.items():
        marker = " <== BEST" if k == best_name else ""
        print(f"  {k}: {v*100:.2f}%{marker}")
    
    # Save the best model (B or C)
    if results['C: Extended + deep'] <= results['B: Extended + 5-95%']:
        print("\nSaving Experiment C models...")
        joblib.dump(xgb_c, 'master_xgb_v5.joblib')
        joblib.dump(lgb_c, 'master_lgb_v5.joblib')
        joblib.dump(enc_c, 'master_encoder_v5.joblib')
        joblib.dump(km_c, 'master_kmeans_v5.joblib')
    else:
        print("\nSaving Experiment B models...")
        joblib.dump(xgb_b, 'master_xgb_v5.joblib')
        joblib.dump(lgb_b, 'master_lgb_v5.joblib')
        joblib.dump(enc_b, 'master_encoder_v5.joblib')
        joblib.dump(km_b, 'master_kmeans_v5.joblib')
    print("Done.")
