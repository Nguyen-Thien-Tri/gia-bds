import pandas as pd
import numpy as np
import joblib

def predict_price(property_data):
    """
    property_data: dict containing keys: 
    ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 
     'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào', 'Mô tả']
    """
    model_xgb = joblib.load('model_xgb_final.joblib')
    model_lgb = joblib.load('model_lgb_final.joblib')
    encoder = joblib.load('encoder_final.joblib')
    
    df = pd.DataFrame([property_data])
    
    # Feature extraction from Description
    desc = df['Mô tả'].astype(str).str.lower()
    df['feat_oto'] = desc.str.contains('ô tô|o to|xe hơi|xe hoi|vào nhà|vaonha').astype(int)
    df['feat_kinh_doanh'] = desc.str.contains('kinh doanh|buôn bán|sầm uất|shop').astype(int)
    df['feat_view'] = desc.str.contains('view hồ|gần hồ|thoáng mát|công viên').astype(int)
    df['feat_no_hau'] = desc.str.contains('nở hậu|no hau').astype(int)
    df['feat_phan_lo'] = desc.str.contains('phân lô|vỉa hè').astype(int)
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    
    features = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 
                'feat_oto', 'feat_kinh_doanh', 'feat_view', 'feat_no_hau', 'feat_phan_lo',
                'type_dist', 'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào']
    
    # Fill missing
    for col in features:
        if col not in df.columns:
            df[col] = 0 if col not in ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'type_dist'] else 'Unknown'
    
    # Encode
    df_encoded = encoder.transform(df[features])
    
    # Predict
    p_xgb = np.expm1(model_xgb.predict(df_encoded))
    p_lgb = np.expm1(model_lgb.predict(df_encoded))
    
    return 0.6 * p_xgb[0] + 0.4 * p_lgb[0]

if __name__ == "__main__":
    sample = {
        'Loại BĐS': 'nhà riêng',
        'Quận': 'Đống Đa',
        'Phường Xã Thị trấn': 'Phường Láng Hạ',
        'Diện tích': 50,
        'Tọa độ x': 21.015,
        'Tọa độ y': 105.815,
        'Số tầng': 4,
        'Số phòng ngủ': 3,
        'Số phòng tắm - vệ sinh': 3,
        'Mặt tiền': 4,
        'Đường vào': 3,
        'Mô tả': 'Nhà đẹp phố Láng Hạ, ô tô vào nhà, kinh doanh tốt, nở hậu.'
    }
    
    price = predict_price(sample)
    print(f"Predicted Price: {price:,.0f} VNĐ (~ {price/1e9:.2f} tỷ)")
