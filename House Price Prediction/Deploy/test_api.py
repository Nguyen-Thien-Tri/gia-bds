"""Quick test script for house price prediction API."""
import json
import sys
from prediction import load_models, predict_price

# Load models
print("Loading models...")
model_xgb, model_lgb, encoder, kmeans, meta = load_models()
print(f"Models loaded. MAPE: {meta['mape']}")
print(f"XGB weight: {meta['xgb_weight']}, LGB weight: {meta['lgb_weight']}")
print(f"Number of features: {len(meta['features'])}")
print()

# Test prediction with sample data
sample = {
    "Loại BĐS": "nhà riêng",
    "Quận": "Đống Đa",
    "Địa chỉ 1": "Phường Láng Hạ",
    "Diện tích": 50.0,
    "Tọa độ x": 21.015,
    "Tọa độ y": 105.815,
    "Số tầng": 4,
    "Số phòng ngủ": 3,
    "Số phòng tắm - vệ sinh": 2,
    "Mặt tiền": 4.0,
    "Đường vào": 3.0,
    "Hướng nhà": "Đông",
    "Hướng ban công": "Tây Nam",
    "Pháp lý": "Sổ đỏ",
    "Nội thất": "Đầy đủ",
    "Căn góc": "Không",
    "Mô tả": "Nhà đẹp phố Láng Hạ, ô tô vào nhà, kinh doanh tốt, nở hậu.",
}

print("Running prediction...")
price = predict_price(sample, model_xgb, model_lgb, encoder, kmeans, meta)
print(f"Predicted price: {price:,.0f} VND ({price/1e9:.2f} tỷ VND)")
print()

# Test with minimal fields
print("Testing with minimal fields...")
minimal = {
    "Loại BĐS": "chung cư",
    "Quận": "Cầu Giấy",
    "Địa chỉ 1": "",
    "Diện tích": 70.0,
    "Tọa độ x": 21.030,
    "Tọa độ y": 105.800,
    "Mô tả": "",
}
price2 = predict_price(minimal, model_xgb, model_lgb, encoder, kmeans, meta)
print(f"Predicted price (minimal): {price2:,.0f} VND ({price2/1e9:.2f} tỷ VND)")

print("\n✅ All tests passed!")