import pandas as pd
import numpy as np
import joblib
import re
from underthesea import text_normalize

STREET_PRICES = {
    'Hoàn Kiếm': {
        'Đinh Tiên Hoàng': 695, 'Lê Thái Tổ': 695, 'Hàng Khay': 695, 'Hàng Đào': 600, 'Hàng Ngang': 600,
        'Hàng Bài': 500, 'Hàng Khoai': 600, 'Hàng Lược': 500, 'Đồng Xuân': 600
    },
    'Ba Đình': {'Phan Đình Phùng': 450, 'Kim Mã': 170, 'Giảng Võ': 170},
    'Cầu Giấy': {'Cầu Giấy': 181, 'Hoàng Đạo Thúy': 147},
    'Thanh Xuân': {'Nguyễn Trãi': 100, 'Lê Văn Lương': 100},
    'Đống Đa': {'Xã Đàn': 180, 'Láng Hạ': 160}
}
DISTRICT_BENCHMARKS = {
    'Hoàn Kiếm': 400, 'Ba Đình': 150, 'Hai Bà Trưng': 130, 'Đống Đa': 130, 'Cầu Giấy': 120,
    'Tây Hồ': 110, 'Thanh Xuân': 90, 'Nam Từ Liêm': 80, 'Bắc Từ Liêm': 70, 'Long Biên': 60
}
METRO_STATIONS = [
    (21.028, 105.828), (21.015, 105.820), (21.015, 105.810), 
    (21.030, 105.800), (21.002, 105.815), (20.975, 105.776)
]

def predict_single(property_data):
    m_xgb = joblib.load('master_xgb_v4.joblib')
    m_lgb = joblib.load('master_lgb_v4.joblib')
    encoder = joblib.load('master_encoder_v4.joblib')
    kmeans = joblib.load('master_kmeans_v4.joblib')
    
    df = pd.DataFrame([property_data])
    df['clean_desc'] = df['Mô tả'].astype(str).apply(text_normalize).str.lower()
    desc = df['clean_desc']
    
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
    
    px, py = property_data['Tọa độ x'], property_data['Tọa độ y']
    df['dist_to_metro'] = min([np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS])
    
    dist, addr = property_data['Quận'], str(property_data['Địa chỉ 2']).lower()
    benchmark = DISTRICT_BENCHMARKS.get(dist, 30)
    if dist in STREET_PRICES:
        for s, p in STREET_PRICES[dist].items():
            if s.lower() in addr: benchmark = p; break
    df['street_benchmark'] = benchmark
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    df['loc_cluster'] = kmeans.predict(df[['Tọa độ x', 'Tọa độ y']])
    
    features = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y', 
                'feat_kinh_doanh', 'feat_mat_tien', 'street_benchmark', 'dist_to_metro',
                'type_dist', 'loc_cluster', 'feat_bien', 'feat_goc', 'feat_oto', 'feat_tranh', 
                'feat_no_hau', 'feat_cong_vien', 'feat_sieu_thi', 'feat_benh_vien', 'feat_tttm', 'feat_thang_may']
    
    X_enc = encoder.transform(df[features])
    p_xgb = np.expm1(m_xgb.predict(X_enc))
    p_lgb = np.expm1(m_lgb.predict(X_enc))
    
    return 0.6 * p_xgb[0] + 0.4 * p_lgb[0]

if __name__ == "__main__":
    property_info = {
        'Loại BĐS': 'nhà mặt phố',
        'Quận': 'Hoàn Kiếm',
        'Địa chỉ 2': 'Phố Hàng Khoai, Phường Đồng Xuân, Quận Hoàn Kiếm, Hà Nội',
        'Phường Xã Thị trấn': 'Phường Đồng Xuân',
        'Diện tích': 100,
        'Tọa độ x': 21.0388511518125,
        'Tọa độ y': 105.849753878157,
        'Số tầng': 4,
        'Số phòng ngủ': 4,
        'Mô tả': 'Siêu Khan Hiếm, nhà mặt phố Hàng Khoai DT 100m2 full thổ cư, 1 sổ 1 chủ. Ngay ngã tư Hàng Lược khu vực kinh doanh sầm uất bậc nhất quận Hoàn Kiếm. Mặt tiền: 5m Hậu: 5.5m (nở hậu, phong thủy tốt). Kết cấu: Nhà xây 4 tầng chắc chắn. Vị trí vàng phố cổ, gần chợ Đồng Xuân.'
    }
    price = predict_single(property_info)
    with open('valuation_result.txt', 'w') as f:
        f.write(f"{price}")
