import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
import lightgbm as lgb
import category_encoders as ce
import joblib
from sklearn.cluster import MiniBatchKMeans
from underthesea import text_normalize

# Street Price Benchmarks
STREET_PRICES = {
    'Hoàn Kiếm': {'Đinh Tiên Hoàng': 695, 'Lê Thái Tổ': 695, 'Hàng Khay': 695, 'Hàng Đào': 600, 'Hàng Ngang': 600},
    'Ba Đình': {'Phan Đình Phùng': 450, 'Kim Mã': 170, 'Giảng Võ': 170, 'Liễu Giai': 180},
    'Cầu Giấy': {'Cầu Giấy': 181, 'Hoàng Đạo Thúy': 147, 'Duy Tân': 121},
    'Thanh Xuân': {'Nguyễn Trãi': 100, 'Lê Văn Lương': 100},
    'Hai Bà Trưng': {'Bà Triệu': 450, 'Phố Huế': 450},
    'Đống Đa': {'Xã Đàn': 180, 'Láng Hạ': 160}
}
DISTRICT_BENCHMARKS = {
    'Hoàn Kiếm': 400, 'Ba Đình': 150, 'Hai Bà Trưng': 130, 'Đống Đa': 130, 'Cầu Giấy': 120,
    'Tây Hồ': 110, 'Thanh Xuân': 90, 'Nam Từ Liêm': 80, 'Bắc Từ Liêm': 70, 'Long Biên': 60,
    'Hà Đông': 50, 'Hoàng Mai': 60
}

# Metro Stations (Hanoi Line 2A & 3)
METRO_STATIONS = [
    (21.028, 105.828), # Cat Linh
    (21.015, 105.820), # Thai Ha
    (21.015, 105.810), # Lang
    (21.030, 105.800), # Cau Giay
    (21.002, 105.815), # Nga Tu So
    (20.975, 105.776), # Ha Dong
]

def get_dist_to_metro(row):
    px, py = row['Tọa độ x'], row['Tọa độ y']
    dists = [np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS]
    return min(dists)

def extract_v4_features(df):
    print("Normalizing text and extracting features...")
    # Normalize desc
    df['clean_desc'] = df['Mô tả'].astype(str).apply(text_normalize).str.lower()
    desc = df['clean_desc']
    
    # User requested keywords
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
    
    # Metro proximity
    df['dist_to_metro'] = df.apply(get_dist_to_metro, axis=1)
    
    # Street benchmark
    def get_benchmark(r):
        dist, addr = r['Quận'], str(r['Địa chỉ 2']).lower()
        if dist in STREET_PRICES:
            for s, p in STREET_PRICES[dist].items():
                if s.lower() in addr: return p
        return DISTRICT_BENCHMARKS.get(dist, 30)
    df['street_benchmark'] = df.apply(get_benchmark, axis=1)
    
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    
    return df

def train_master():
    print("Loading data...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    for col in ['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Số phòng ngủ']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    
    # Extreme cleaning
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
    
    df = extract_v4_features(df)
    
    # Clustering
    kmeans = MiniBatchKMeans(n_clusters=250, random_state=42, n_init=3)
    df['loc_cluster'] = kmeans.fit_predict(df[['Tọa độ x', 'Tọa độ y']])
    
    features = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 
                'feat_kinh_doanh', 'feat_mat_tien', 'street_benchmark', 'dist_to_metro',
                'type_dist', 'loc_cluster', 'feat_bien', 'feat_goc', 'feat_oto', 'feat_tranh', 
                'feat_no_hau', 'feat_cong_vien', 'feat_sieu_thi', 'feat_benh_vien', 'feat_tttm', 'feat_thang_may']
    
    categorical = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'type_dist', 'loc_cluster']
    
    X = df[features]
    y = np.log1p(df['Khoảng giá'])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
    encoder = ce.TargetEncoder(cols=categorical)
    X_train_enc = encoder.fit_transform(X_train, y_train)
    X_test_enc = encoder.transform(X_test)
    
    print("Training V4 Ensemble (Metro + NLP Normalization)...")
    model_xgb = xgb.XGBRegressor(n_estimators=3500, learning_rate=0.02, max_depth=13, tree_method='hist')
    model_xgb.fit(X_train_enc, y_train)
    model_lgb = lgb.LGBMRegressor(n_estimators=3500, learning_rate=0.02, num_leaves=1023, verbose=-1)
    model_lgb.fit(X_train_enc, y_train)
    
    y_pred = 0.6 * np.expm1(model_xgb.predict(X_test_enc)) + 0.4 * np.expm1(model_lgb.predict(X_test_enc))
    final_mape = mean_absolute_percentage_error(np.expm1(y_test), y_pred)
    print(f"\nFINAL V4 MAPE: {final_mape*100:.2f}%")
    
    joblib.dump(model_xgb, 'master_xgb_v4.joblib')
    joblib.dump(model_lgb, 'master_lgb_v4.joblib')
    joblib.dump(encoder, 'master_encoder_v4.joblib')
    joblib.dump(kmeans, 'master_kmeans_v4.joblib')

if __name__ == "__main__":
    train_master()
