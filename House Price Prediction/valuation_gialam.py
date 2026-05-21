import pandas as pd
import numpy as np
import joblib
import re
from underthesea import text_normalize

STREET_PRICES = {
    'Gia Lâm': {
        'Cửu Việt': 45, 'Trâu Quỳ': 50, 'Ngô Xuân Quảng': 60
    }
}
DISTRICT_BENCHMARKS = {
    'Gia Lâm': 35, 'Hoàn Kiếm': 400, 'Ba Đình': 150, 'Cầu Giấy': 120
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
        'Quận': 'Gia Lâm',
        'Địa chỉ 2': 'Đường Cửu Việt 2, Thị trấn Trâu Quỳ, Huyện Gia Lâm, Hà Nội',
        'Phường Xã Thị trấn': 'Thị trấn Trâu Quỳ',
        'Diện tích': 80,
        'Tọa độ x': 21.0090425483874,
        'Tọa độ y': 105.937651268846,
        'Số tầng': 3,
        'Số phòng ngủ': 3,
        'Mô tả': 'Nhà mặt tiền kinh doanh - đường 7m vỉa hè 2m. Đường oto tránh có vỉa hè. Trung tâm khu sinh viên hàng xóm đều là các cửa hàng. Vị trí vùng lõi Gia Lâm, gần cổng trường học viện nông nghiệp, cạnh Vinocenpard 1.'
    }
    price = predict_single(property_info)
    with open('valuation_result_gialam.txt', 'w') as f:
        f.write(f"{price}")
