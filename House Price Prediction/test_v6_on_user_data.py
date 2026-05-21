import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_absolute_percentage_error
from underthesea import text_normalize

# Constants from V6
METRO_STATIONS = [(21.028, 105.828), (21.015, 105.820), (21.015, 105.810), (21.030, 105.800), (21.002, 105.815), (20.975, 105.776)]
DISTRICT_BENCHMARKS = {'Hoàn Kiếm': 400, 'Ba Đình': 150, 'Hai Bà Trưng': 130, 'Đống Đa': 130, 'Cầu Giấy': 120,
                       'Tây Hồ': 110, 'Thanh Xuân': 90, 'Nam Từ Liêm': 80, 'Bắc Từ Liêm': 70, 'Long Biên': 60,
                       'Hà Đông': 50, 'Hoàng Mai': 60, 'Gia Lâm': 35, 'Đông Anh': 30, 'Sóc Sơn': 20}
STREET_PRICES = {
    'Hoàn Kiếm': {'Đinh Tiên Hoàng': 695, 'Lê Thái Tổ': 695, 'Hàng Khay': 695, 'Hàng Đào': 600,
                  'Hàng Ngang': 600, 'Hàng Khoai': 600, 'Hàng Lược': 500, 'Đồng Xuân': 600},
    'Ba Đình': {'Phan Đình Phùng': 450, 'Kim Mã': 170, 'Giảng Võ': 170, 'Liễu Giai': 180},
    'Cầu Giấy': {'Cầu Giấy': 181, 'Hoàng Đạo Thúy': 147, 'Duy Tân': 121},
    'Thanh Xuân': {'Nguyễn Trãi': 100, 'Lê Văn Lương': 100},
    'Hai Bà Trưng': {'Bà Triệu': 450, 'Phố Huế': 450},
    'Đống Đa': {'Xã Đàn': 180, 'Láng Hạ': 160}
}
CENTER_LAT, CENTER_LON = 21.0285, 105.8542

def get_dist_to_metro(px, py):
    return min([np.sqrt((px-mx)**2 + (py-my)**2) for mx, my in METRO_STATIONS])

def get_benchmark(dist, addr):
    if dist in STREET_PRICES:
        for s, p in STREET_PRICES[dist].items():
            if s.lower() in addr: return p
    return DISTRICT_BENCHMARKS.get(dist, 25)

def extract_features_v6(df):
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
    df['feat_noi_that'] = desc.str.contains('nội thất|đầy đủ|tiện nghi').astype(int)
    df['feat_an_ninh'] = desc.str.contains('an ninh|bảo vệ|camera').astype(int)
    df['feat_view'] = desc.str.contains('view|hồ|sông').astype(int)
    df['feat_so_do'] = desc.str.contains('sổ đỏ|sổ hồng').astype(int)
    df['feat_chinh_chu'] = desc.str.contains('chính chủ').astype(int)
    
    df['dist_to_metro'] = df.apply(lambda r: get_dist_to_metro(r['Tọa độ x'], r['Tọa độ y']), axis=1)
    df['dist_to_center'] = np.sqrt((df['Tọa độ x'] - CENTER_LAT)**2 + (df['Tọa độ y'] - CENTER_LON)**2)
    df['street_benchmark'] = df.apply(lambda r: get_benchmark(r['Quận'], str(r['Địa chỉ 2']).lower()), axis=1)
    df['type_dist'] = df['Loại BĐS'].astype(str) + "_" + df['Quận'].astype(str)
    
    for col in ['Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['dien_tich_per_tang'] = df['Diện tích'] / df['Số tầng'].replace(0, 1)
    df['mat_tien_x_tang'] = df['Mặt tiền'] * df['Số tầng']
    return df

def test_on_data():
    print("Loading test data...")
    # Using specific encoding to handle the garbled names if possible, otherwise just use column indices
    X_raw = pd.read_csv('HaNoiXtestData.csv', encoding='utf-8')
    y_raw = pd.read_csv('HaNoiYtestData.csv')
    
    # Mapping raw columns to standard names
    # Column indices based on Get-Content check:
    # 0: Loai quang cao, 1: Loai BDS, 2: Tinh/TP, 3: Quan, 4: Dia chi 1, 6: Dien tich
    # 7: So PN, 14: dia_chi_2, 16: Mo_ta, 17: Phuong, 18: Toa_do_x, 19: Toa_do_y, 20: so_tang, 21: mat_tien, 22: duong_vao
    
    col_mapping = {
        X_raw.columns[1]: 'Loại BĐS',
        X_raw.columns[3]: 'Quận',
        'Phuong': 'Phường Xã Thị trấn',
        'dia_chi_2': 'Địa chỉ 2',
        X_raw.columns[6]: 'Diện tích',
        'Toa_do_x': 'Tọa độ x',
        'Toa_do_y': 'Tọa độ y',
        'so_tang': 'Số tầng',
        X_raw.columns[7]: 'Số phòng ngủ',
        'mat_tien': 'Mặt tiền',
        'duong_vao': 'Đường vào',
        'Mo_ta': 'Mô tả'
    }
    X_raw = X_raw.rename(columns=col_mapping)
    
    # Fill NaN to avoid KMeans error
    for col in ['Diện tích', 'Tọa độ x', 'Tọa độ y']:
        X_raw[col] = pd.to_numeric(X_raw[col], errors='coerce').fillna(X_raw[col].median() if not X_raw[col].isna().all() else 0)
    
    # Extract V6 features
    X_processed = extract_features_v6(X_raw)
    
    # Load V6 assets
    print("Loading V6 models and assets...")
    m_xgb = joblib.load('master_xgb_v6.joblib')
    m_lgb = joblib.load('master_lgb_v6.joblib')
    encoder = joblib.load('master_encoder_v6.joblib')
    kmeans = joblib.load('master_kmeans_v6.joblib')
    
    X_processed['loc_cluster'] = kmeans.predict(X_processed[['Tọa độ x', 'Tọa độ y']])
    
    ALL_FEATURES = ['Loại BĐS', 'Quận', 'Phường Xã Thị trấn', 'Diện tích', 'Tọa độ x', 'Tọa độ y',
                    'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào',
                    'feat_kinh_doanh', 'feat_mat_tien', 'street_benchmark', 'dist_to_metro', 'dist_to_center',
                    'type_dist', 'loc_cluster',
                    'feat_bien', 'feat_goc', 'feat_oto', 'feat_tranh', 'feat_no_hau',
                    'feat_cong_vien', 'feat_sieu_thi', 'feat_benh_vien', 'feat_tttm', 'feat_thang_may',
                    'feat_noi_that', 'feat_an_ninh', 'feat_view', 'feat_so_do', 'feat_chinh_chu',
                    'dien_tich_per_tang', 'mat_tien_x_tang']
    
    X_enc = encoder.transform(X_processed[ALL_FEATURES])
    
    # Weights from V6 summary
    w_xgb = 0.70
    w_lgb = 0.30
    
    print("Predicting...")
    p_xgb = np.expm1(m_xgb.predict(X_enc))
    p_lgb = np.expm1(m_lgb.predict(X_enc))
    y_pred = w_xgb * p_xgb + w_lgb * p_lgb
    
    # Y data is in millions
    y_true = y_raw['mean_unique_khoang_gia_million'] * 1e6
    
    mape = mean_absolute_percentage_error(y_true, y_pred)
    print(f"\nMAPE on provided test data: {mape*100:.2f}%")

if __name__ == "__main__":
    test_on_data()
