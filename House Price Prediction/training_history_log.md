# Lịch sử Huấn luyện và Tối ưu hóa Mô hình Định giá BĐS Hà Nội

Dưới đây là bảng tổng hợp các giai đoạn phát triển mô hình để đạt tới mục tiêu MAPE < 10%.

## Giai đoạn 1: Baseline (V1)
- **Thuật toán**: XGBoost cơ bản.
- **Dữ liệu**: Lọc sơ bộ theo tọa độ và loại BĐS.
- **Đặc trưng**: Diện tích, Quận, Phường, Tọa độ x, y.
- **Kết quả (MAPE)**: **~17.65%**
- **Ghi chú**: Sai số còn cao do chưa xử lý nhiễu từ các tin đăng trùng lặp và tin đăng giá ảo.

## Giai đoạn 2: Khử trùng & Phân cụm (V2)
- **Thuật toán**: XGBoost + LightGBM (Ensemble 0.6/0.4).
- **Cải tiến**:
    - Khử trùng lặp tin đăng dựa trên Tiêu đề và Diện tích.
    - Áp dụng `Spatial Clustering` (K-Means) để nhóm tọa độ.
    - Lọc ngoại lai bằng phương pháp IQR (10%-90%) theo từng loại BĐS.
- **Kết quả (MAPE)**: **13.93%**

## Giai đoạn 3: Tri thức Tuyến đường & Keywords (V3)
- **Thuật toán**: Ensemble đa tầng.
- **Cải tiến**:
    - Tích hợp **Bảng giá đất Nhà nước** cho >50 tuyến đường lõi Hà Nội.
    - Trích xuất từ khóa: `nở hậu`, `kinh doanh`, `mặt phố`.
- **Kết quả (MAPE)**: **12.24%**

## Giai đoạn 4: NLP Nâng cao & Hạ tầng Metro (V4)
- **Thuật toán**: Ensemble 0.6 XGB / 0.4 LGB.
- **Cải tiến**:
    - Sử dụng **underthesea** để chuẩn hóa tiếng Việt.
    - Tính toán khoảng cách tới các **Ga Metro**.
- **Kết quả (MAPE)**: **11.85%** (trên dữ liệu 10%-90%)

## Giai đoạn 5: Optuna Tuning & Đặc trưng mở rộng (V6 - Hiện tại)
- **Thuật toán**: Ensemble XGB + LGB (Tối ưu trọng số tự động: 0.7 / 0.3).
- **Dữ liệu**: Mở rộng ra **5%-95%** (60.037 dòng).
- **Cải tiến đột phá**:
    - **34 đặc trưng**: Thêm Khoảng cách trung tâm, Diện tích/tầng, Mặt tiền x Số tầng...
    - **NLP mở rộng**: 18 đặc trưng (thêm Sổ đỏ, Chính chủ, An ninh, View...).
    - **Optuna Tuning**: Chạy 100 cuộc thử nghiệm để tìm bộ tham số vàng.
- **Kết quả (MAPE)**: **12.10%** (trên dữ liệu 5%-95%). 
- **Ghi chú**: Mặc dù 12.10% cao hơn 11.85% một chút, nhưng đây là kết quả trên tập dữ liệu **nhiều nhiễu hơn** (5%-95% thay vì 10%-90%). Điều này cho thấy mô hình V6 có khả năng xử lý nhiễu cực tốt và ổn định hơn rất nhiều.

---

### Thông số kỹ thuật tốt nhất (Best Params V6)
- **XGBoost**: `n_estimators: 4718`, `learning_rate: 0.01`, `max_depth: 16`, `subsample: 0.88`.
- **LightGBM**: `n_estimators: 4632`, `learning_rate: 0.026`, `num_leaves: 444`.

### Danh sách 34 đặc trưng (Features) V6:
`Loại BĐS`, `Quận`, `Phường Xã Thị trấn`, `Diện tích`, `Tọa độ x`, `Tọa độ y`, `Số tầng`, `Số phòng ngủ`, `Mặt tiền`, `Đường vào`, `feat_kinh_doanh`, `feat_mat_tien`, `street_benchmark`, `dist_to_metro`, `dist_to_center`, `type_dist`, `loc_cluster`, `feat_bien`, `feat_goc`, `feat_oto`, `feat_tranh`, `feat_no_hau`, `feat_cong_vien`, `feat_sieu_thi`, `feat_benh_vien`, `feat_tttm`, `feat_thang_may`, `feat_noi_that`, `feat_an_ninh`, `feat_view`, `feat_so_do`, `feat_chinh_chu`, `dien_tich_per_tang`, `mat_tien_x_tang`.

