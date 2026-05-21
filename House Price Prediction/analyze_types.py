import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
import category_encoders as ce

def analysis():
    df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
    
    col_price = 'Khoảng giá'
    col_area = 'Diện tích'
    col_type = 'Loại BĐS'
    
    df[col_price] = pd.to_numeric(df[col_price], errors='coerce')
    df[col_area] = pd.to_numeric(df[col_area], errors='coerce')
    df = df.dropna(subset=[col_price, col_area])
    
    # Same filters as before
    df = df[(df[col_price] >= 5e8) & (df[col_price] <= 2e11)]
    df = df[(df[col_area] >= 15) & (df[col_area] <= 1000)]
    
    df['ppm'] = df[col_price] / df[col_area]
    df = df[(df['ppm'] >= 1.5e7) & (df['ppm'] <= 8e8)]
    
    # Analysis per type
    results = {}
    for t in df[col_type].unique():
        sub = df[df[col_type] == t]
        if len(sub) < 100: continue
        
        # Simple train/test
        X = sub[['Diện tích', 'Tọa độ x', 'Tọa độ y']]
        y = np.log1p(sub[col_price])
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = xgb.XGBRegressor(n_estimators=500, learning_rate=0.05, max_depth=8, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = np.expm1(model.predict(X_test))
        y_test_orig = np.expm1(y_test)
        mape = mean_absolute_percentage_error(y_test_orig, y_pred)
        results[t] = mape
        
    with open('type_analysis.txt', 'w', encoding='utf-8') as f:
        for t, m in results.items():
            f.write(f"{t}: {m*100:.2f}%\n")

if __name__ == "__main__":
    analysis()
