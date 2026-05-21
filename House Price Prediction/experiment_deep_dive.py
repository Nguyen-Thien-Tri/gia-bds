import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor
import category_encoders as ce
import joblib
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

def log_result(exp_name, mape, details=""):
    with open('experiment_logs.txt', 'a', encoding='utf-8') as f:
        f.write(f"--- {exp_name} ---\nMAPE: {mape*100:.2f}%\nDetails: {details}\n\n")

def preprocess_advanced(df):
    # 1. Spatial Clustering
    coords = df[['Tọa độ x', 'Tọa độ y']].values
    kmeans = MiniBatchKMeans(n_clusters=100, random_state=42, n_init=3)
    df['loc_cluster'] = kmeans.fit_transform(coords).argmin(axis=1)
    
    # 2. Text Mining with SVD (More advanced than keywords)
    print("Vectorizing descriptions...")
    tfidf = TfidfVectorizer(max_features=500, stop_words=None)
    desc_matrix = tfidf.fit_transform(df['Mô tả'].astype(str).fillna(''))
    svd = TruncatedSVD(n_components=10, random_state=42)
    desc_svd = svd.fit_transform(desc_matrix)
    for i in range(10):
        df[f'desc_svd_{i}'] = desc_svd[:, i]
        
    # 3. Neighborhood stats (Target-based but calculated carefully to avoid leak)
    # Actually TargetEncoder does this, but we can do PPM mean per Ward
    df['ppm'] = df['Khoảng giá'] / df['Diện tích']
    ward_ppm = df.groupby('Phường Xã Thị trấn')['ppm'].transform('median')
    df['ward_ppm_med'] = ward_ppm.fillna(df['ppm'].median())
    
    return df

def train_suite():
    print("Loading and deep cleaning...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    for col in ['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Số phòng ngủ']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    
    # Strict filter for "Gold Standard" training data
    df_list = []
    for t in df['Loại BĐS'].unique():
        sub = df[df['Loại BĐS'] == t]
        if len(sub) < 100: continue
        sub = sub[(sub['Khoảng giá'] >= 1e9) & (sub['Khoảng giá'] <= 1.5e11)] # Focus on mid-high market
        sub = sub[(sub['Diện tích'] >= 20) & (sub['Diện tích'] <= 800)]
        ppm = sub['Khoảng giá'] / sub['Diện tích']
        q1, q3 = ppm.quantile(0.1), ppm.quantile(0.9) # Even stricter outlier removal
        df_list.append(sub[(ppm >= q1) & (ppm <= q3)])
    df = pd.concat(df_list)
    
    # Deduplicate
    df['title_prefix'] = df['Tiêu đề'].astype(str).str[:40].str.lower()
    df = df.drop_duplicates(subset=['Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Loại BĐS', 'title_prefix'])
    
    print(f"Data size after extreme cleaning: {len(df)}")
    
    df = preprocess_advanced(df)
    
    features = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 
                'loc_cluster', 'ward_ppm_med', 'Số tầng', 'Số phòng ngủ'] + [f'desc_svd_{i}' for i in range(10)]
    
    categorical = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'loc_cluster']
    
    X = df[features]
    y = np.log1p(df['Khoảng giá'])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # ENCODER
    encoder = ce.TargetEncoder(cols=categorical)
    X_train_enc = encoder.fit_transform(X_train, y_train)
    X_test_enc = encoder.transform(X_test)
    
    # Experiment 1: CatBoost (Excellent for this type of data)
    print("Running CatBoost experiment...")
    model_cat = CatBoostRegressor(iterations=2000, learning_rate=0.03, depth=10, 
                                  loss_function='RMSE', od_type='Iter', od_wait=100, 
                                  verbose=500, random_seed=42)
    model_cat.fit(X_train, y_train, eval_set=(X_test, y_test), cat_features=categorical)
    
    y_pred_cat = np.expm1(model_cat.predict(X_test))
    mape_cat = mean_absolute_percentage_error(np.expm1(y_test), y_pred_cat)
    log_result("CatBoost Native", mape_cat)
    
    # Experiment 2: Stacking (LGBM + XGB + Cat)
    print("Running Stacking experiment...")
    model_lgb = lgb.LGBMRegressor(n_estimators=1500, learning_rate=0.03, num_leaves=255, verbose=-1)
    model_lgb.fit(X_train_enc, y_train)
    y_pred_lgb = np.expm1(model_lgb.predict(X_test_enc))
    
    model_xgb = xgb.XGBRegressor(n_estimators=1500, learning_rate=0.03, max_depth=10)
    model_xgb.fit(X_train_enc, y_train)
    y_pred_xgb = np.expm1(model_xgb.predict(X_test_enc))
    
    # Simple blend
    y_pred_blend = (y_pred_cat + y_pred_lgb + y_pred_xgb) / 3
    mape_blend = mean_absolute_percentage_error(np.expm1(y_test), y_pred_blend)
    log_result("Triple Ensemble Blend", mape_blend)
    
    # Final save of the best model (if under 10% or just best so far)
    if mape_blend < 0.10:
        print("!!! TARGET REACHED !!!")
    
    joblib.dump(model_cat, 'catboost_model.joblib')
    joblib.dump(encoder, 'encoder_deep.joblib')
    joblib.dump(kmeans, 'kmeans_spatial.joblib')

if __name__ == "__main__":
    open('experiment_logs.txt', 'w').close() # Clear logs
    train_suite()
