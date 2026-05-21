import pandas as pd
import numpy as np
import joblib
import re

# Benchmark Data (Same as used in training)
STREET_PRICES = {
    'Hoàn Kiếm': {
        'Đinh Tiên Hoàng': 695, 'Lê Thái Tổ': 695, 'Hàng Khay': 695, 'Hàng Đào': 600, 'Hàng Ngang': 600,
        'Hai Bà Trưng': 550, 'Lý Thường Kiệt': 500, 'Trần Hưng Đạo': 500, 'Phố Huế': 450, 'Hàng Bài': 500
    },
    'Ba Đình': {
        'Phan Đình Phùng': 450, 'Kim Mã': 170, 'Giảng Võ': 170, 'Liễu Giai': 180, 'Đội Cấn': 120, 'Nguyễn Thái Học': 200
    },
    'Cầu Giấy': {
        'Cầu Giấy': 181, 'Hoàng Đạo Thúy': 147, 'Duy Tân': 121, 'Hoàng Quốc Việt': 130, 'Trung Hòa': 130, 'Trần Duy Hưng': 150
    },
    'Thanh Xuân': {
        'Nguyễn Trãi': 100, 'Lê Văn Lương': 100, 'Ngụy Như Kon Tum': 80, 'Khuất Duy Tiến': 90
    },
    'Hai Bà Trưng': {
        'Bà Triệu': 450, 'Phố Huế': 450, 'Bạch Mai': 120, 'Đại Cồ Việt': 140, 'Minh Khai': 100, 'Trương Định': 80
    },
    'Đống Đa': {
        'Nguyễn Lương Bằng': 160, 'Xã Đàn': 180, 'Tôn Đức Thắng': 160, 'Chùa Bộc': 150, 'Thái Hà': 150, 'Láng Hạ': 160
    },
    'Nam Từ Liêm': {
        'Hàm Nghi': 100, 'Mễ Trì': 80, 'Lê Đức Thọ': 80, 'Tố Hữu': 80
    }
}
DISTRICT_BENCHMARKS = {
    'Hoàn Kiếm': 400, 'Ba Đình': 150, 'Hai Bà Trưng': 130, 'Đống Đa': 130, 'Cầu Giấy': 120,
    'Tây Hồ': 110, 'Thanh Xuân': 90, 'Nam Từ Liêm': 80, 'Bắc Từ Liêm': 70, 'Long Biên': 60,
    'Hà Đông': 50, 'Hoàng Mai': 60, 'Gia Lâm': 30, 'Đông Anh': 25, 'Thanh Trì': 25, 'Hoài Đức': 20
}

def get_street_benchmark(district, address):
    addr_lower = str(address).lower()
    if district in STREET_PRICES:
        for street, price in STREET_PRICES[district].items():
            if street.lower() in addr_lower:
                return price
    return DISTRICT_BENCHMARKS.get(district, 30)

def predict_price_enriched(property_data):
    """
    property_data: dict with keys ['Loại BĐS', 'Quận', 'Địa chỉ 2', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Số phòng ngủ', 'Mô tả']
    """
    m_xgb = joblib.load('master_xgb_v3.joblib')
    m_lgb = joblib.load('master_lgb_v3.joblib')
    encoder = joblib.load('master_encoder_v3.joblib')
    kmeans = joblib.load('master_kmeans_v3.joblib')
    
    df = pd.DataFrame([property_data])
    
    # Feature Extraction
    desc = df['Mô tả'].astype(str).str.lower()
    def get_width(text):
        match = re.search(r'ngõ (?:rộng )?(\d+(?:\.\d+)?)m', text)
        if match: return float(match.group(1))
        if 'ô tô tránh' in text: return 5.0
        if 'ô tô' in text: return 4.0
        return 2.5
    
    df['feat_alley_width'] = desc.apply(get_width)
    df['feat_kinh_doanh'] = desc.str.contains('kinh doanh|buôn bán|văn phòng|shop').astype(int)
    df['feat_mat_tien'] = desc.str.contains('mặt phố|mặt đường|shophouse').astype(int)
    df['street_benchmark'] = df.apply(lambda r: get_street_benchmark(r['Quận'], r['Địa chỉ 2']), axis=1)
    df['floor_area_ratio'] = df['Số tầng'] / (df['Diện tích'] + 1)
    df['room_area_ratio'] = df['Số phòng ngủ'] / (df['Diện tích'] + 1)
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    df['loc_cluster'] = kmeans.predict(df[['Tọa độ x', 'Tọa độ y']])
    
    features = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 
                'feat_alley_width', 'feat_kinh_doanh', 'feat_mat_tien', 'street_benchmark',
                'floor_area_ratio', 'room_area_ratio', 'type_dist', 'loc_cluster']
    
    for col in features:
        if col not in df.columns:
            df[col] = 0 if col not in ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'type_dist'] else 'Unknown'
            
    X_enc = encoder.transform(df[features])
    
    p_xgb = np.expm1(m_xgb.predict(X_enc))
    p_lgb = np.expm1(m_lgb.predict(X_enc))
    
    return 0.6 * p_xgb[0] + 0.4 * p_lgb[0]

if __name__ == "__main__":
    sample = {
        'Loại BĐS': 'nhà mặt phố',
        'Quận': 'Hoàn Kiếm',
        'Địa chỉ 2': 'Phố Hàng Đào, Hoàn Kiếm, Hà Nội',
        'Phường Xã Thị trấn': 'Phường Hàng Đào',
        'Diện tích': 80,
        'Tọa độ x': 21.033,
        'Tọa độ y': 105.852,
        'Số tầng': 4,
        'Số phòng ngủ': 5,
        'Mô tả': 'Vị trí kinh doanh đắc địa nhất phố cổ Hàng Đào.'
    }
    price = predict_price_enriched(sample)
    print(f"Enriched Predicted Price: {price:,.0f} VNĐ (~ {price/1e9:.2f} tỷ)")
