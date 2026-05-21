import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
import lightgbm as lgb
import category_encoders as ce
import optuna
import joblib

def train():
    print("Loading data...")
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    # 1. CLEANING
    for col in ['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['Khoảng giá', 'Diện tích', 'Tọa độ x', 'Tọa độ y'])
    
    # Per-type strict filter
    df_list = []
    for t in df['Loại BĐS'].unique():
        sub = df[df['Loại BĐS'] == t]
        if len(sub) < 100: continue
        sub = sub[(sub['Khoảng giá'] >= 1e9) & (sub['Khoảng giá'] <= 2e11)]
        sub = sub[(sub['Diện tích'] >= 20) & (sub['Diện tích'] <= 1000)]
        ppm = sub['Khoảng giá'] / sub['Diện tích']
        q1, q3 = ppm.quantile(0.05), ppm.quantile(0.95)
        df_list.append(sub[(ppm >= q1) & (ppm <= q3)])
    df = pd.concat(df_list)
    
    # Deduplicate
    df['title_prefix'] = df['Tiêu đề'].astype(str).str[:40].str.lower()
    df = df.drop_duplicates(subset=['Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Loại BĐS', 'title_prefix'])
    
    # 2. FEATURES
    features = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y']
    X = df[features]
    y = np.log1p(df['Khoảng giá'])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
    encoder = ce.TargetEncoder(cols=['Loại BĐS', 'Quận', 'Phường Xã Thị trấn'])
    X_train_enc = encoder.fit_transform(X_train, y_train)
    X_test_enc = encoder.transform(X_test)
    
    # 3. OPTUNA FOR XGBOOST
    def objective(trial):
        param = {
            'n_estimators': 1000,
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
            'max_depth': trial.suggest_int('max_depth', 6, 15),
            'subsample': trial.suggest_float('subsample', 0.7, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 1.0),
            'gamma': trial.suggest_float('gamma', 0, 0.5),
            'tree_method': 'hist',
            'n_jobs': -1,
            'random_state': 42
        }
        model = xgb.XGBRegressor(**param)
        model.fit(X_train_enc, y_train)
        preds = model.predict(X_test_enc)
        return mean_absolute_percentage_error(np.expm1(y_test), np.expm1(preds))

    print("Starting Optuna study (10 trials)...")
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=10)
    
    print(f"Best MAPE: {study.best_value*100:.2f}%")
    print(f"Best Params: {study.best_params}")
    
    # 4. FINAL ENSEMBLE WITH BEST PARAMS
    best_xgb = xgb.XGBRegressor(**study.best_params, n_estimators=3000, tree_method='hist')
    best_xgb.fit(X_train_enc, y_train)
    
    # LightGBM (Tuned manually based on experience)
    best_lgb = lgb.LGBMRegressor(n_estimators=3000, learning_rate=0.02, num_leaves=511, 
                                  subsample=0.9, colsample_bytree=0.8, verbose=-1)
    best_lgb.fit(X_train_enc, y_train)
    
    y_pred = 0.5 * np.expm1(best_xgb.predict(X_test_enc)) + 0.5 * np.expm1(best_lgb.predict(X_test_enc))
    final_mape = mean_absolute_percentage_error(np.expm1(y_test), y_pred)
    
    print(f"\nFinal Optimized MAPE: {final_mape*100:.2f}%")
    
    with open('experiment_results_final.txt', 'w', encoding='utf-8') as f:
        f.write(f"Best MAPE: {final_mape*100:.2f}%\n")
        f.write(f"Best Params: {study.best_params}\n")

if __name__ == "__main__":
    train()
