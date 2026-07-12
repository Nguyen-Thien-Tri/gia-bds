"""
House Price Prediction Module - FastAPI
Model: XGBoost + LightGBM ensemble (final version)
"""
import pandas as pd
import numpy as np
import joblib
import os

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))


def load_models():
    """Load all model artifacts from the Deploy directory."""
    model_xgb = joblib.load(os.path.join(MODEL_DIR, "model_xgb_final.joblib"))
    model_lgb = joblib.load(os.path.join(MODEL_DIR, "model_lgb_final.joblib"))
    encoder = joblib.load(os.path.join(MODEL_DIR, "encoder_final.joblib"))
    return model_xgb, model_lgb, encoder


def predict_price(property_data, model_xgb, model_lgb, encoder):
    """
    Predict house price.
    
    Parameters
    ----------
    property_data : dict
        Input features with keys:
        - 'Loại BĐS' (str): e.g. "nhà riêng", "căn hộ chung cư", "đất", "nhà mặt phố"
        - 'Quận' (str): District name, e.g. "Đống Đa", "Cầu Giấy", "Hoàn Kiếm"
        - 'Phường Xã Thị trấn' (str): Ward name
        - 'Diện tích' (float): Area in m²
        - 'Tọa độ x' (float): Latitude
        - 'Tọa độ y' (float): Longitude
        - 'Số tầng' (float, optional): Number of floors
        - 'Số phòng ngủ' (float, optional): Number of bedrooms
        - 'Mặt tiền' (float, optional): Frontage width (m)
        - 'Đường vào' (float, optional): Alley width (m)
        - 'Mô tả' (str, optional): Property description text
    
    Returns
    -------
    float
        Predicted price in VND
    """
    df = pd.DataFrame([property_data])

    # Feature extraction from Description
    desc = df.get("Mô tả", pd.Series([""])).astype(str).str.lower()
    df["feat_oto"] = desc.str.contains("ô tô|o to|xe hơi|xe hoi|vào nhà|vaonha").astype(int)
    df["feat_kinh_doanh"] = desc.str.contains("kinh doanh|buôn bán|sầm uất|shop").astype(int)
    df["feat_view"] = desc.str.contains("view hồ|gần hồ|thoáng mát|công viên").astype(int)
    df["feat_no_hau"] = desc.str.contains("nở hậu|no hau").astype(int)
    df["feat_phan_lo"] = desc.str.contains("phân lô|vỉa hè").astype(int)
    df["type_dist"] = df["Loại BĐS"].astype(str) + "_" + df["Quận"].astype(str)

    features = [
        "Loại BĐS", "Quận", "Phường Xã Thị trấn", "Diện tích", "Tọa độ x", "Tọa độ y",
        "feat_oto", "feat_kinh_doanh", "feat_view", "feat_no_hau", "feat_phan_lo",
        "type_dist", "Số tầng", "Số phòng ngủ", "Mặt tiền", "Đường vào",
    ]

    # Fill missing columns with defaults
    for col in features:
        if col not in df.columns:
            if col in ["Loại BĐS", "Quận", "Phường Xã Thị trấn", "type_dist"]:
                df[col] = "Unknown"
            else:
                df[col] = 0

    # Ensure numeric types
    numeric_cols = [
        "Diện tích", "Tọa độ x", "Tọa độ y",
        "Số tầng", "Số phòng ngủ", "Mặt tiền", "Đường vào",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Encode
    df_encoded = encoder.transform(df[features])

    # Predict (log-space → exp)
    p_xgb = np.expm1(model_xgb.predict(df_encoded))
    p_lgb = np.expm1(model_lgb.predict(df_encoded))

    # Blend: 60% XGBoost + 40% LightGBM
    return float(0.6 * p_xgb[0] + 0.4 * p_lgb[0])