"""
House Price Prediction Module - FastAPI
Model: XGBoost + LightGBM ensemble V11
"""
import json
import numpy as np
import pandas as pd
import joblib
import os

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Models")

# ── Hanoi metro stations & center (from V10/V11) ────────
METRO_STATIONS = [
    (21.028, 105.828), (21.015, 105.820), (21.015, 105.810),
    (21.030, 105.800), (21.002, 105.815), (20.975, 105.776),
]
CENTER_LAT, CENTER_LON = 21.0285, 105.8542


def _get_dist_to_metro(px, py):
    return min(np.sqrt((px - mx) ** 2 + (py - my) ** 2) for mx, my in METRO_STATIONS)


def load_models():
    """Load all model artifacts from the Models/ subdirectory."""
    model_xgb = joblib.load(os.path.join(MODEL_DIR, "master_xgb_v11.joblib"))
    model_lgb = joblib.load(os.path.join(MODEL_DIR, "master_lgb_v11.joblib"))
    encoder = joblib.load(os.path.join(MODEL_DIR, "master_encoder_v11.joblib"))
    kmeans = joblib.load(os.path.join(MODEL_DIR, "master_kmeans_v11.joblib"))

    with open(os.path.join(MODEL_DIR, "model_meta_v11.json"), "r") as f:
        meta = json.load(f)

    return model_xgb, model_lgb, encoder, kmeans, meta


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the full V11 feature engineering pipeline on raw input data.
    Modifies df in-place and returns it.
    """
    # Standardise description text
    desc = df.get("Mô tả", pd.Series([""] * len(df))).astype(str).str.lower()

    # ── NLP binary features from description ──────────────
    df["feat_oto"] = desc.str.contains("xe hơi|ô tô|oto").astype(int)
    df["feat_tranh"] = desc.str.contains("tránh").astype(int)
    df["feat_no_hau"] = desc.str.contains("nở hậu").astype(int)
    df["feat_thang_may"] = desc.str.contains("thang máy").astype(int)
    df["feat_kinh_doanh"] = desc.str.contains("kinh doanh|buôn bán").astype(int)
    df["feat_mat_tien"] = desc.str.contains("mặt phố|mặt đường").astype(int)
    df["feat_noi_that"] = desc.str.contains("nội thất|đầy đủ|tiện nghi").astype(int)
    df["feat_so_do"] = desc.str.contains("sổ đỏ|sổ hồng").astype(int)
    df["feat_chinh_chu"] = desc.str.contains("chính chủ").astype(int)
    df["feat_view_nui"] = desc.str.contains("view núi|view đồi").astype(int)
    df["feat_view_ho_song"] = desc.str.contains("view hồ|view sông|sát hồ|ven hồ").astype(int)
    df["feat_view_canh_dong"] = desc.str.contains("view cánh đồng|cánh đồng").astype(int)
    df["feat_khuon_vien"] = desc.str.contains("sẵn ao|vườn cây|cây ăn trái|nhà vườn").astype(int)
    df["feat_nghi_duong"] = desc.str.contains("nghỉ dưỡng|homestay|farmstay|villa").astype(int)
    df["feat_nha_xuong"] = desc.str.contains("nhà xưởng").astype(int)
    df["feat_phan_lo"] = desc.str.contains("phân lô").astype(int)
    df["feat_f0"] = desc.str.contains("f0|chưa qua đầu tư").astype(int)
    df["feat_san_nha"] = desc.str.contains("sẵn nhà|nhà cấp 4|ở ngay").astype(int)
    df["feat_duong_nhua"] = desc.str.contains("đường nhựa").astype(int)
    df["feat_duong_betong"] = desc.str.contains("đường bê tông").astype(int)
    df["feat_truc_chinh"] = desc.str.contains("trục chính|đường tỉnh|tỉnh lộ|quốc lộ|đường lớn").astype(int)
    df["feat_phap_ly_chuan"] = desc.str.contains("sẵn sổ|sang tên luôn|pháp lý chuẩn").astype(int)
    df["feat_du_lich"] = desc.str.contains("khu du lịch|resort").astype(int)
    df["feat_truong_hoc"] = desc.str.contains("trường học").astype(int)
    df["feat_cho"] = desc.str.contains("chợ").astype(int)
    df["feat_nga_ba_tu"] = desc.str.contains("ngã 3|ngã 4|ngã tư").astype(int)
    df["feat_view_bien"] = desc.str.contains("view biển|biển").astype(int)
    df["feat_goc"] = desc.str.contains("góc").astype(int)
    df["feat_cong_vien"] = desc.str.contains("công viên").astype(int)
    df["feat_sieu_thi"] = desc.str.contains("siêu thị|big c").astype(int)
    df["feat_benh_vien"] = desc.str.contains("bệnh viện").astype(int)
    df["feat_tttm"] = desc.str.contains("trung tâm thương mại|tttm|aeon|vincom").astype(int)
    df["feat_nha_moi"] = desc.str.contains("nhà mới|xây mới|mới xây").astype(int)
    df["feat_cai_tao"] = desc.str.contains("cải tạo|sửa").astype(int)
    df["feat_nha_cu"] = desc.str.contains("nhà cũ").astype(int)
    df["feat_nhieu_mat_tien"] = desc.str.contains("nhiều mặt tiền").astype(int)
    df["feat_mat_tien_sau"] = desc.str.contains("mặt tiền sau").astype(int)

    # ── can_goc (Căn góc) ─────────────────────────────────
    df["can_goc"] = (
        df.get("Căn góc", pd.Series([""] * len(df)))
        .astype(str)
        .str.lower()
        .isin(["có", "yes", "1", "true", "căn góc"])
    ).astype(int)

    # ── Spatial features ─────────────────────────────────
    df["dist_to_metro"] = df.apply(
        lambda r: _get_dist_to_metro(
            pd.to_numeric(r.get("Tọa độ x", np.nan), errors="coerce") or 0,
            pd.to_numeric(r.get("Tọa độ y", np.nan), errors="coerce") or 0,
        ),
        axis=1,
    )
    df["dist_to_center"] = np.sqrt(
        (df["Tọa độ x"] - CENTER_LAT) ** 2 + (df["Tọa độ y"] - CENTER_LON) ** 2
    )

    # ── Interaction features ──────────────────────────────
    floors = pd.to_numeric(df.get("Số tầng", pd.Series([0] * len(df))), errors="coerce").fillna(1)
    floors = floors.replace(0, 1)
    df["dien_tich_per_tang"] = df["Diện tích"] / floors
    frontage = pd.to_numeric(df.get("Mặt tiền", pd.Series([0] * len(df))), errors="coerce").fillna(0)
    df["mat_tien_x_tang"] = frontage * floors

    # ── type_dist (composite key) ─────────────────────────
    df["type_dist"] = df["Loại BĐS"].astype(str) + "_" + df["Quận"].astype(str)

    return df


def predict_price(property_data, model_xgb, model_lgb, encoder, kmeans, meta):
    """
    Predict house price using V11 ensemble models.

    Parameters
    ----------
    property_data : dict
        Input features (must contain at minimum the core fields).
    model_xgb, model_lgb : trained models
    encoder : fitted category_encoders.TargetEncoder
    kmeans : fitted MiniBatchKMeans (for loc_cluster)
    meta : dict with 'features' list, 'xgb_weight', 'lgb_weight'

    Returns
    -------
    float
        Predicted price in VND
    """
    FEATURES = meta["features"]
    xgb_weight = meta["xgb_weight"]
    lgb_weight = meta["lgb_weight"]

    df = pd.DataFrame([property_data])

    # ── Ensure all required core columns exist ────────────
    expected_input_cols = {
        "Loại BĐS", "Quận", "Địa chỉ 1", "Diện tích", "Tọa độ x", "Tọa độ y",
        "Số tầng", "Số phòng ngủ", "Số phòng tắm - vệ sinh",
        "Mặt tiền", "Đường vào", "Hướng nhà", "Hướng ban công",
        "Pháp lý", "Nội thất", "Căn góc", "Mô tả",
    }
    for col in expected_input_cols:
        if col not in df.columns:
            if col in ("Loại BĐS", "Quận", "Địa chỉ 1", "Hướng nhà", "Hướng ban công", "Pháp lý", "Nội thất"):
                df[col] = "Unknown"
            elif col in ("Căn góc",):
                df[col] = "Không"
            else:
                df[col] = 0

    # ── Coerce numeric types ──────────────────────────────
    numeric_cols = [
        "Diện tích", "Tọa độ x", "Tọa độ y",
        "Số tầng", "Số phòng ngủ", "Số phòng tắm - vệ sinh",
        "Mặt tiền", "Đường vào",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ── Feature engineering ───────────────────────────────
    df = extract_features(df)

    # ── loc_cluster via kmeans ────────────────────────────
    coords = df[["Tọa độ x", "Tọa độ y"]].fillna(
        df[["Tọa độ x", "Tọa độ y"]].median()
    )
    df["loc_cluster"] = kmeans.predict(coords)

    # ── Ensure all expected features exist ────────────────
    for col in FEATURES:
        if col not in df.columns:
            if col in ("type_dist",):
                df[col] = "Unknown"
            else:
                df[col] = 0

    # ── Encode ────────────────────────────────────────────
    df_encoded = encoder.transform(df[FEATURES])

    # ── Predict (log-space → exp) ─────────────────────────
    p_xgb = np.expm1(model_xgb.predict(df_encoded))
    p_lgb = np.expm1(model_lgb.predict(df_encoded))

    # ── Weighted blend ────────────────────────────────────
    return float(xgb_weight * p_xgb[0] + lgb_weight * p_lgb[0])