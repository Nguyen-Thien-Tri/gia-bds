import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.preprocessing import QuantileTransformer
from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import RidgeCV
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor
import category_encoders as ce
import joblib
from underthesea import text_normalize
from sklearn.cluster import MiniBatchKMeans

# Benchmarks and Metro Data (kept from V4)
METRO_STATIONS = [(21.028, 105.828), (21.015, 105.820), (21.015, 105.810), (21.030, 105.800), (21.002, 105.815), (20.975, 105.776)]
DISTRICT_BENCHMARKS = {'Hoàn Kiếm': 400, 'Ba Đình': 150, 'Hai Bà Trưng': 130, 'Đống Đa': 130, 'Cầu Giấy': 120, 'Tây Hồ': 110, 'Thanh Xuân': 90, 'Nam Từ Liêm': 80, 'Bắc Từ Liêm': 70, 'Long Biên': 60, 'Hà Đông': 50, 'Hoàng Mai': 60}

def get_dist_to_metro(px, py):
    return min([np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS])

def preprocess_v5(df):
    print("V5 Preprocessing...")
    df['clean_desc'] = df['Mô tả'].astype(str).apply(text_normalize).str.lower()
    desc = df['clean_desc']
    
    # Feature engineering
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
    
    df['dist_to_metro'] = df.apply(lambda r: get_dist_to_metro(r['Tọa độ x'], r['Tọa độ y']), axis=1)
    df['street_benchmark'] = df['Quận'].map(DISTRICT_BENCHMARKS).fillna(30)
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    
    return df

def train_v5():
    print("Loading and cleaning (5%-95% balance)...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    for col in ['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Số phòng ngủ']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    
    # Use 5%-95% as a middle ground for research
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
    df = df.sort_values('Ngày đăng').drop_duplicates(subset=['Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Loại BĐS', 'title_prefix'], keep='last')
    
    df = preprocess_v5(df)
    
    # Clustering
    kmeans = MiniBatchKMeans(n_clusters=300, random_state=42, n_init=3)
    df['loc_cluster'] = kmeans.fit_predict(df[['Tọa độ x', 'Tọa độ y']])
    
    features = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 
                'feat_kinh_doanh', 'feat_mat_tien', 'street_benchmark', 'dist_to_metro',
                'type_dist', 'loc_cluster', 'feat_bien', 'feat_goc', 'feat_oto', 'feat_tranh', 
                'feat_no_hau', 'feat_cong_vien', 'feat_sieu_thi', 'feat_benh_vien', 'feat_tttm', 'feat_thang_may']
    
    categorical = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'type_dist', 'loc_cluster']
    
    X = df[features]
    y = df['Khoảng giá']
    
    # Advanced Target Transformation: Quantile
    qt = QuantileTransformer(output_distribution='normal', random_state=42)
    y_trans = qt.fit_transform(y.values.reshape(-1, 1)).flatten()
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_trans, test_size=0.15, random_state=42)
    
    # Encoder
    encoder = ce.TargetEncoder(cols=categorical)
    X_train_enc = encoder.fit_transform(X_train, y_train)
    X_test_enc = encoder.transform(X_test)
    
    # Base Estimators for Stacking
    estimators = [
        ('xgb', xgb.XGBRegressor(n_estimators=2000, learning_rate=0.03, max_depth=12, tree_method='hist')),
        ('lgb', lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=511, verbose=-1)),
        ('cat', CatBoostRegressor(iterations=2000, learning_rate=0.03, depth=10, verbose=False))
    ]
    
    print("Training V5 Stacking Ensemble (XGB + LGB + Cat)...")
    stack = StackingRegressor(
        estimators=estimators,
        final_estimator=RidgeCV(),
        cv=KFold(n_splits=5, shuffle=True, random_state=42),
        n_jobs=-1
    )
    
    # CatBoost needs some features as strings if not encoded, but we use encoded data here for simplicity in stacking
    stack.fit(X_train_enc, y_train)
    
    # Predict and Inverse Transform
    y_pred_trans = stack.predict(X_test_enc)
    y_pred = qt.inverse_transform(y_pred_trans.reshape(-1, 1)).flatten()
    y_true = qt.inverse_transform(y_test.reshape(-1, 1)).flatten()
    
    mape = mean_absolute_percentage_error(y_true, y_pred)
    print(f"\nFINAL V5 STACKING MAPE: {mape*100:.2f}%")
    
    joblib.dump(stack, 'master_stack_v5.joblib')
    joblib.dump(qt, 'quantile_trans_v5.joblib')
    joblib.dump(encoder, 'encoder_v5.joblib')
    joblib.dump(kmeans, 'kmeans_v5.joblib')

if __name__ == "__main__":
    train_v5()
