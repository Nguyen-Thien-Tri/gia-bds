import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
import lightgbm as lgb
import category_encoders as ce
import joblib

def extract_features(df):
    desc = df['Mô tả'].astype(str).str.lower()
    # Advanced keywords
    df['feat_oto'] = desc.str.contains('ô tô|o to|xe hơi|xe hoi|vào nhà|vaonha').astype(int)
    df['feat_kinh_doanh'] = desc.str.contains('kinh doanh|buôn bán|sầm uất|shop').astype(int)
    df['feat_view'] = desc.str.contains('view hồ|gần hồ|thoáng mát|công viên').astype(int)
    df['feat_no_hau'] = desc.str.contains('nở hậu|no hau').astype(int)
    df['feat_phan_lo'] = desc.str.contains('phân lô|vỉa hè').astype(int)
    
    # Interaction
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    
    return df

def train():
    print("Loading data...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    for col in ['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    
    # Stricter outlier removal per type (5th to 95th percentile)
    print("Quality filtering...")
    df_clean_list = []
    for t in df['Loại BĐS'].unique():
        sub = df[df['Loại BĐS'] == t]
        if len(sub) < 100: continue
        sub = sub[(sub['Khoảng giá'] >= 5e8) & (sub['Khoảng giá'] <= 3e11)]
        sub = sub[(sub['Diện tích'] >= 15) & (sub['Diện tích'] <= 1000)]
        ppm = sub['Khoảng giá'] / sub['Diện tích']
        q1, q3 = ppm.quantile(0.05), ppm.quantile(0.95)
        sub = sub[(ppm >= q1) & (ppm <= q3)]
        df_clean_list.append(sub)
    df = pd.concat(df_clean_list)
    
    print("Deduplicating...")
    df['title_prefix'] = df['Tiêu đề'].astype(str).str[:40].str.lower()
    df['Ngày đăng'] = pd.to_datetime(df['Ngày đăng'], errors='coerce')
    df = df.sort_values('Ngày đăng').drop_duplicates(
        subset=['Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Loại BĐS', 'title_prefix'], 
        keep='last'
    )
    
    df = extract_features(df)
    
    features = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 
                'feat_oto', 'feat_kinh_doanh', 'feat_view', 'feat_no_hau', 'feat_phan_lo',
                'type_dist', 'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào']
    
    X = df[features]
    y = np.log1p(df['Khoảng giá'])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
    print("Encoding...")
    categorical = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'type_dist']
    encoder = ce.TargetEncoder(cols=categorical)
    X_train_enc = encoder.fit_transform(X_train, y_train)
    X_test_enc = encoder.transform(X_test)
    
    # Ensemble Models
    print("Training XGBoost...")
    model_xgb = xgb.XGBRegressor(n_estimators=2500, learning_rate=0.02, max_depth=12, 
                                 subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=42)
    model_xgb.fit(X_train_enc, y_train)
    
    print("Training LightGBM...")
    model_lgb = lgb.LGBMRegressor(n_estimators=2500, learning_rate=0.02, num_leaves=255, 
                                  subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=42, verbose=-1)
    model_lgb.fit(X_train_enc, y_train)
    
    # Weighted Average
    y_pred_xgb = np.expm1(model_xgb.predict(X_test_enc))
    y_pred_lgb = np.expm1(model_lgb.predict(X_test_enc))
    
    # Optimize weights slightly (0.6 XGB + 0.4 LGB usually works)
    y_pred = 0.6 * y_pred_xgb + 0.4 * y_pred_lgb
    y_test_orig = np.expm1(y_test)
    
    mape = mean_absolute_percentage_error(y_test_orig, y_pred)
    print(f"\nFINAL ENSEMBLE MAPE: {mape * 100:.2f}%")
    
    if mape < 0.12:
        print("Excellent Accuracy Reached!")
    
    joblib.dump(model_xgb, 'model_xgb_final.joblib')
    joblib.dump(model_lgb, 'model_lgb_final.joblib')
    joblib.dump(encoder, 'encoder_final.joblib')

if __name__ == "__main__":
    train()
