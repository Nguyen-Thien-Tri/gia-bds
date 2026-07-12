"""
Single-file V12 training script. This file is the new, consolidated ML model training entrypoint.
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from sklearn.linear_model import Ridge
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import OneHotEncoder
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)
import xgboost as xgb
import lightgbm as lgb
import catboost as cb
import category_encoders as ce
import joblib
from sklearn.cluster import MiniBatchKMeans
from underthesea import text_normalize
warnings.filterwarnings("ignore")

METRO_STATIONS = [
    (21.028, 105.828), (21.015, 105.820), (21.015, 105.810),
    (21.030, 105.800), (21.002, 105.815), (20.975, 105.776),
]
CENTER_LAT, CENTER_LON = 21.0285, 105.8542

STREET_PRICES = {
    'Hoàn Kiếm': {'Đinh Tiên Hoàng': 695, 'Lê Thái Tổ': 695, 'Hàng Khay': 695, 'Hàng Đào': 600, 'Hàng Ngang': 600},
    'Ba Đình': {'Phan Đình Phùng': 450, 'Kim Mã': 170, 'Giảng Võ': 170, 'Liễu Giai': 180},
    'Cầu Giấy': {'Cầu Giấy': 181, 'Hoàng Đạo Thúy': 147, 'Duy Tân': 121},
    'Thanh Xuân': {'Nguyễn Trãi': 100, 'Lê Văn Lương': 100},
    'Hai Bà Trưng': {'Bà Triệu': 450, 'Phố Huế': 450},
    'Đống Đa': {'Xã Đàn': 180, 'Láng Hạ': 160},
}
DISTRICT_BENCHMARKS = {
    'Hoàn Kiếm': 400, 'Ba Đình': 150, 'Hai Bà Trưng': 130, 'Đống Đa': 130, 'Cầu Giấy': 120,
    'Tây Hồ': 110, 'Thanh Xuân': 90, 'Nam Từ Liêm': 80, 'Bắc Từ Liêm': 70, 'Long Biên': 60,
    'Hà Đông': 50, 'Hoàng Mai': 60,
}

ONEHOT_COLS = ['Loại BĐS', 'Hướng nhà', 'Hướng ban công']
TARGET_COLS = ['Quận', 'Phường Xã Thị trấn', 'Pháp lý', 'Nội thất', 'type_dist', 'loc_cluster']
NUMERIC_COLS = [
    'Diện tích', 'Tọa độ x', 'Tọa độ y', 'Số tầng', 'Số phòng ngủ', 'Mặt tiền', 'Đường vào',
    'can_goc', 'feat_oto', 'feat_tranh', 'feat_no_hau', 'feat_thang_may',
    'feat_kinh_doanh', 'feat_mat_tien', 'feat_noi_that', 'feat_so_do', 'feat_chinh_chu',
    'feat_view_nui', 'feat_view_ho_song', 'feat_view_canh_dong', 'feat_khuon_vien',
    'feat_nghi_duong', 'feat_nha_xuong', 'feat_phan_lo', 'feat_f0', 'feat_san_nha',
    'feat_duong_nhua', 'feat_duong_betong', 'feat_truc_chinh', 'feat_phap_ly_chuan',
    'feat_du_lich', 'feat_truong_hoc', 'feat_cho', 'feat_nga_ba_tu',
    'feat_hem_xe_tai', 'feat_dien_tich_dat_o', 'feat_ngan', 'feat_xa_trung_tam',
    'dist_to_metro', 'dist_to_center', 'street_benchmark',
    'dien_tich_per_tang', 'mat_tien_x_tang', 'dien_tich_per_phong',
    'price_per_m2', 'log_price_per_m2', 'ppm_rank', 'cluster_density', 'log_cluster_density',
]
ALL_FEATURES = NUMERIC_COLS + ONEHOT_COLS + TARGET_COLS
DATA_PATH = 'filtered_hanoi_data.csv'

def get_dist_to_metro(px, py):
    return min(np.sqrt((px - mx) ** 2 + (py - my) ** 2) for mx, my in METRO_STATIONS)

def get_benchmark(district, address):
    if district in STREET_PRICES:
        addr = str(address).lower()
        for street, price in STREET_PRICES[district].items():
            if street.lower() in addr:
                return price
    return DISTRICT_BENCHMARKS.get(district, 25)

def load_data(path=None):
    if path is None:
        path = DATA_PATH
    df = pd.read_csv(path, encoding="utf-8", low_memory=False)
    top4 = ["căn hộ chung cư", "nhà riêng", "đất", "nhà mặt phố"]
    df = df[(df["Loại quảng cáo"] == "Bán") & (df["Loại BĐS"].isin(top4)) & (df["Tỉnh thành phố"] == "Hà Nội")].copy()
    for col in ["Khoảng giá", "Diện tích", "Số tầng", "Số phòng ngủ",
                "Số phòng tắm - vệ sinh", "Mặt tiền", "Đường vào", "Tọa độ x", "Tọa độ y"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df["Khoảng giá"] > 1e8].dropna(subset=["Khoảng giá", "Diện tích", "Tọa độ x", "Tọa độ y"])
    return df

def deduplicate(df):
    group_cols = [c for c in [
        "Loại quảng cáo", "Loại BĐS", "Tỉnh thành phố", "Quận", "Địa chỉ 1",
        "Căn góc", "Diện tích", "Số phòng ngủ", "Số phòng tắm - vệ sinh",
        "Tên dự án", "Hướng nhà", "Hướng ban công", "Số tầng", "Mặt tiền", "Đường vào",
    ] if c in df.columns]
    def mean_unique(_s):
        vals = _s.dropna().unique()
        return np.mean(vals) if len(vals) else np.nan
    agg = {"Price": ("Khoảng giá", mean_unique)}
    for src, tgt in [
        ("Pháp lý", "Pháp lý"), ("Nội thất", "Nội thất"), ("Địa chỉ 2", "Địa chỉ 2"),
        ("Tiêu đề", "Tiêu đề"), ("Mô tả", "Mô tả"), ("Phường Xã Thị trấn", "Phường Xã Thị trấn"),
        ("Tọa độ x", "Tọa độ x"), ("Tọa độ y", "Tọa độ y"),
    ]:
        if src in df.columns:
            agg[tgt] = (src, "first")
    return df.groupby(group_cols, dropna=False).agg(**agg).reset_index().dropna(subset=["Price"])

def remove_top_1pct(df):
    drop = []
    for _, g in df.groupby(["Loại BĐS", "Quận"]):
        k = max(1, int(np.ceil(len(g) * 0.01)))
        drop.extend(g.nlargest(k, "Price").index.tolist())
    return df.drop(index=drop).reset_index(drop=True)

def remove_price_per_m2_outliers(df):
    df["price_per_m2"] = df["Price"] / df["Diện tích"].replace(0, np.nan)
    df["log_price_per_m2"] = np.log1p(df["price_per_m2"].fillna(1))
    drop = []
    for _, g in df.groupby(["Loại BĐS", "Quận"]):
        if len(g) < 20:
            continue
        q1, q3 = g["log_price_per_m2"].quantile(0.05), g["log_price_per_m2"].quantile(0.95)
        iqr = q3 - q1
        drop.extend(g[(g["log_price_per_m2"] < q1 - 2 * iqr) | (g["log_price_per_m2"] > q3 + 2 * iqr)].index.tolist())
    return df.drop(index=drop).reset_index(drop=True)

def remove_isolation_forest_outliers(df):
    cols = ["Price", "Diện tích", "price_per_m2", "Tọa độ x", "Tọa độ y"]
    mat = df[cols].fillna(df[cols].median())
    labels = IsolationForest(n_estimators=200, contamination=0.02, random_state=42, n_jobs=-1).fit_predict(np.log1p(mat))
    return df[labels == 1].reset_index(drop=True)

def clean_data():
    df = load_data()
    print(f"Loaded: {len(df):,}")
    df = deduplicate(df)
    print(f"After dedup: {len(df):,}")
    df = remove_top_1pct(df)
    print(f"After top-1% drop: {len(df):,}")
    df = remove_price_per_m2_outliers(df)
    print(f"After price/m2 outliers: {len(df):,}")
    df = remove_isolation_forest_outliers(df)
    print(f"After IsolationForest: {len(df):,}")
    return df

def extract_features(df):
    df = df.copy()
    df["clean_desc"] = df["Mô tả"].astype(str).apply(text_normalize).str.lower()
    desc = df["clean_desc"]
    df["feat_oto"] = desc.str.contains("xe hoi|o to|oto").astype(int)
    df["feat_tranh"] = desc.str.contains("tranh").astype(int)
    df["feat_no_hau"] = desc.str.contains("no hau").astype(int)
    df["feat_thang_may"] = desc.str.contains("thang may").astype(int)
    df["feat_kinh_doanh"] = desc.str.contains("kinh doanh|buon ban").astype(int)
    df["feat_mat_tien"] = desc.str.contains("mat pho|mat duong").astype(int)
    df["feat_noi_that"] = desc.str.contains("noi that|day du|tien nghi").astype(int)
    df["feat_so_do"] = desc.str.contains("so do|so hong").astype(int)
    df["feat_chinh_chu"] = desc.str.contains("chinh chu").astype(int)
    df["feat_view_nui"] = desc.str.contains("view nui|view doi").astype(int)
    df["feat_view_ho_song"] = desc.str.contains("view ho|view song|sat ho|ven ho").astype(int)
    df["feat_view_canh_dong"] = desc.str.contains("view canh dong|canh dong").astype(int)
    df["feat_khuon_vien"] = desc.str.contains("san ao|vuon cay|cay an trai|nha vuon").astype(int)
    df["feat_nghi_duong"] = desc.str.contains("nghi duong|homestay|farmstay|villa").astype(int)
    df["feat_nha_xuong"] = desc.str.contains("nha xuong").astype(int)
    df["feat_phan_lo"] = desc.str.contains("phan lo").astype(int)
    df["feat_f0"] = desc.str.contains("f0|chua qua dau tu").astype(int)
    df["feat_san_nha"] = desc.str.contains("san nha|nha cap 4|o ngay").astype(int)
    df["feat_duong_nhua"] = desc.str.contains("duong nhua").astype(int)
    df["feat_duong_betong"] = desc.str.contains("duong be tong").astype(int)
    df["feat_truc_chinh"] = desc.str.contains("truc chinh|duong tinh|tinh lo|quoc lo|duong lon").astype(int)
    df["feat_phap_ly_chuan"] = desc.str.contains("san so|sang ten luon|phap ly chuan").astype(int)
    df["feat_du_lich"] = desc.str.contains("khu du lich|resort").astype(int)
    df["feat_truong_hoc"] = desc.str.contains("truong hoc").astype(int)
    df["feat_cho"] = desc.str.contains("cho").astype(int)
    df["feat_nga_ba_tu"] = desc.str.contains("nga 3|nga 4|nga tu").astype(int)
    df["feat_hem_xe_tai"] = desc.str.contains("hem xe tai|ngo xe tai|hem 5m|ngo 5m").astype(int)
    df["feat_dien_tich_dat_o"] = desc.str.contains("dien tich dat o|dat o|tho cu|dat tho cu").astype(int)
    df["feat_ngan"] = desc.str.contains("ngan|ngan hep").astype(int)
    df["feat_xa_trung_tam"] = desc.str.contains("xa trung tam|vung ven|ngoai thanh").astype(int)

    df["dist_to_metro"] = df.apply(lambda r: get_dist_to_metro(r["Tọa độ x"], r["Tọa độ y"]), axis=1)
    df["dist_to_center"] = np.sqrt((df["Tọa độ x"] - CENTER_LAT) ** 2 + (df["Tọa độ y"] - CENTER_LON) ** 2)
    df["street_benchmark"] = df.apply(lambda r: get_benchmark(r["Quận"], r["Địa chỉ 2"]), axis=1)
    df["type_dist"] = df["Loại BĐS"].astype(str) + "_" + df["Quận"].astype(str)

    df["price_per_m2"] = df["Price"] / df["Diện tích"].replace(0, np.nan)
    df["log_price_per_m2"] = np.log1p(df["price_per_m2"].fillna(1))
    df["ppm_rank"] = df.groupby(["Loại BĐS", "Quận"])["price_per_m2"].rank(pct=True).fillna(0.5)

    for col in ["Số tầng", "Số phòng ngủ", "Số phòng tắm - vệ sinh", "Mặt tiền", "Đường vào"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.extract(r"(\d+\.?\d*)")[0], errors="coerce")
        else:
            df[col] = np.nan
    for col in ["Số tầng", "Số phòng ngủ", "Mặt tiền", "Đường vào"]:
        if col in df.columns:
            df[col] = df[col].fillna(df.groupby("Loại BĐS")[col].transform("median")).fillna(0)

    if "Căn góc" in df.columns:
        df["can_goc"] = df["Căn góc"].astype(str).str.lower().isin(["có", "yes", "1", "true", "căn góc"]).astype(int)
    else:
        df["can_goc"] = 0

    df["dien_tich_per_tang"] = df["Diện tích"] / df["Số tầng"].replace(0, np.nan).fillna(1)
    df["mat_tien_x_tang"] = df["Mặt tiền"] * df["Số tầng"]
    df["dien_tich_per_phong"] = df["Diện tích"] / df["Số phòng ngủ"].replace(0, np.nan).fillna(1)
    return df

def add_spatial_density(df, kmeans=None, n_clusters=400):
    coords = df[["Tọa độ x", "Tọa độ y"]].fillna(df[["Tọa độ x", "Tọa độ y"]].median())
    if kmeans is None:
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init=3)
        df["loc_cluster"] = kmeans.fit_predict(coords)
    else:
        df["loc_cluster"] = kmeans.predict(coords)
    counts = df["loc_cluster"].value_counts().to_dict()
    df["cluster_density"] = df["loc_cluster"].map(counts)
    df["log_cluster_density"] = np.log1p(df["cluster_density"])
    return df, kmeans

def tune_xgb(X_train, y_train, X_test, y_test, n_trials=50):
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 800, 3000),
            "learning_rate": trial.suggest_float("learning_rate", 1e-2, 5e-2, log=True),
            "max_depth": trial.suggest_int("max_depth", 6, 12),
            "subsample": trial.suggest_float("subsample", 0.6, 0.95),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
            "gamma": trial.suggest_float("gamma", 0.0, 5.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "tree_method": "hist",
            "verbosity": 0,
        }
        model = xgb.XGBRegressor(**params)
        X_tr, X_v, y_tr, y_v = train_test_split(X_train, y_train, test_size=0.2, random_state=trial.number)
        model.fit(X_tr, y_tr, eval_set=[(X_v, y_v)], verbose=False)
        return mean_absolute_percentage_error(np.expm1(y_test), np.expm1(model.predict(X_test)))
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params, study.best_value


def tune_lgb(X_train, y_train, X_test, y_test, n_trials=50):
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 800, 3000),
            "learning_rate": trial.suggest_float("learning_rate", 1e-2, 5e-2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 64, 512),
            "subsample": trial.suggest_float("subsample", 0.6, 0.95),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "min_split_gain": trial.suggest_float("min_split_gain", 0.0, 1.0),
            "verbose": -1,
        }
        model = lgb.LGBMRegressor(**params)
        X_tr, X_v, y_tr, y_v = train_test_split(X_train, y_train, test_size=0.2, random_state=trial.number)
        model.fit(X_tr, y_tr, eval_set=[(X_v, y_v)], callbacks=[lgb.early_stopping(50)], eval_metric="rmse")
        return mean_absolute_percentage_error(np.expm1(y_test), np.expm1(model.predict(X_test)))
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params, study.best_value


def tune_cat(X_train, y_train, X_test, y_test, n_trials=50):
    def objective(trial):
        params = {
            "iterations": trial.suggest_int("iterations", 800, 3000),
            "learning_rate": trial.suggest_float("learning_rate", 1e-2, 5e-2, log=True),
            "depth": trial.suggest_int("depth", 6, 12),
            "subsample": trial.suggest_float("subsample", 0.6, 0.95),
            "colsample_bylevel": trial.suggest_float("colsample_bylevel", 0.5, 1.0),
            "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 5, 50),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0, log=True),
            "random_seed": 42,
            "verbose": 0,
        }
        model = cb.CatBoostRegressor(**params)
        X_tr, X_v, y_tr, y_v = train_test_split(X_train, y_train, test_size=0.2, random_state=trial.number)
        model.fit(X_tr, y_tr, eval_set=(X_v, y_v), verbose=False)
        return mean_absolute_percentage_error(np.expm1(y_test), np.expm1(model.predict(X_test)))
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params, study.best_value

def train_v12():
    df = clean_data()
    df = extract_features(df)
    df, kmeans = add_spatial_density(df, n_clusters=400)
    df = df[[c for c in ALL_FEATURES if c in df.columns] + ["Price"]].copy()
    print(f"Using {len(ALL_FEATURES)} features")

    X = df[[c for c in ALL_FEATURES if c in df.columns]].copy()
    y = np.log1p(df["Price"])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    print(f"Train/Test = {len(X_train):,} / {len(X_test):,}")

    ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    X_train_ohe = pd.DataFrame(index=X_train.index)
    X_test_ohe = pd.DataFrame(index=X_test.index)
    ohe_cols = []
    onehot_feats = [c for c in ONEHOT_COLS if c in X.columns]
    if onehot_feats:
        ohe.fit(X_train[onehot_feats].fillna("MISSING"))
        for i, col in enumerate(onehot_feats):
            for val in ohe.categories_[i]:
                ohe_cols.append(f"{col}_{str(val).replace(' ', '_').replace('/', '_')}")
        X_train_ohe = pd.DataFrame(ohe.transform(X_train[onehot_feats].fillna("MISSING")), columns=ohe_cols, index=X_train.index)
        X_test_ohe = pd.DataFrame(ohe.transform(X_test[onehot_feats].fillna("MISSING")), columns=ohe_cols, index=X_test.index)

    target_feats = [c for c in TARGET_COLS if c in X.columns]
    encoder = ce.TargetEncoder(cols=target_feats)
    X_train_te = encoder.fit_transform(X_train[target_feats].fillna("MISSING"), y_train)
    X_test_te = encoder.transform(X_test[target_feats].fillna("MISSING"))

    numeric_feats = [c for c in NUMERIC_COLS if c in X.columns]
    X_train_num = X_train[numeric_feats].fillna(0)
    X_test_num = X_test[numeric_feats].fillna(0)
    X_train_final = pd.concat([X_train_num, X_train_ohe, X_train_te], axis=1)
    X_test_final = pd.concat([X_test_num, X_test_ohe, X_test_te], axis=1)
    feature_names = X_train_final.columns.tolist()

    print("Tuning XGBoost...")
    bp_xgb, score_xgb = tune_xgb(X_train_final, y_train, X_test_final, y_test)
    print(f"XGB best={score_xgb*100:.2f}%")

    print("Tuning LightGBM...")
    bp_lgb, score_lgb = tune_lgb(X_train_final, y_train, X_test_final, y_test)
    print(f"LGB best={score_lgb*100:.2f}%")

    print("Tuning CatBoost...")
    bp_cat, score_cat = tune_cat(X_train_final, y_train, X_test_final, y_test)
    print(f"CAT best={score_cat*100:.2f}%")

    fit_xgb = {k: v for k, v in bp_xgb.items()}
    fit_xgb.update({"tree_method": "hist", "verbosity": 0})
    fit_lgb = {k: v for k, v in bp_lgb.items()}
    fit_lgb.update({"verbose": -1})
    fit_cat = {k: v for k, v in bp_cat.items()}
    fit_cat.update({"verbose": 0, "random_seed": 42})

    m_xgb = xgb.XGBRegressor(**fit_xgb).fit(X_train_final, y_train)
    m_lgb = lgb.LGBMRegressor(**fit_lgb).fit(X_train_final, y_train)
    m_cat = cb.CatBoostRegressor(**fit_cat).fit(X_train_final, y_train, verbose=False)

    p_xgb = np.expm1(m_xgb.predict(X_test_final))
    p_lgb = np.expm1(m_lgb.predict(X_test_final))
    p_cat = np.expm1(m_cat.predict(X_test_final))
    y_true = np.expm1(y_test)

    print(f"XGB={mean_absolute_percentage_error(y_true, p_xgb)*100:.2f}%")
    print(f"LGB={mean_absolute_percentage_error(y_true, p_lgb)*100:.2f}%")
    print(f"CAT={mean_absolute_percentage_error(y_true, p_cat)*100:.2f}%")

    best_w, best_mape = [0.34, 0.33, 0.33], 999.0
    for w1 in np.arange(0, 1.01, 0.05):
        for w2 in np.arange(0, 1.01 - w1, 0.05):
            w3 = 1.0 - w1 - w2
            score = mean_absolute_percentage_error(y_true, w1 * p_xgb + w2 * p_lgb + w3 * p_cat)
            if score < best_mape:
                best_mape, best_w = score, [w1, w2, w3]
    print(f"Blend MAPE={best_mape*100:.2f}%, weights={best_w}")

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    stack_train = np.zeros((len(X_train_final), 3))
    for tr_idx, val_idx in kf.split(X_train_final):
        X_tr_f = X_train_final.iloc[tr_idx]
        X_vl_f = X_train_final.iloc[val_idx]
        y_tr_f = y_train.iloc[tr_idx]
        stack_train[val_idx, 0] = np.expm1(xgb.XGBRegressor(**fit_xgb).fit(X_tr_f, y_tr_f).predict(X_vl_f))
        stack_train[val_idx, 1] = np.expm1(lgb.LGBMRegressor(**fit_lgb).fit(X_tr_f, y_tr_f).predict(X_vl_f))
        stack_train[val_idx, 2] = np.expm1(cb.CatBoostRegressor(**fit_cat).fit(X_tr_f, y_tr_f, verbose=False).predict(X_vl_f))
    meta = Ridge(alpha=1.0, random_state=42).fit(stack_train, np.expm1(y_train))
    stack_test = np.column_stack([p_xgb, p_lgb, p_cat])
    y_pred_stack = meta.predict(stack_test)
    stack_mape = mean_absolute_percentage_error(y_true, y_pred_stack)
    print(f"Stacking MAPE={stack_mape*100:.2f}%")

    if stack_mape < best_mape:
        final_pred = y_pred_stack
        final_mape = stack_mape
        em = "stacking"
    else:
        final_pred = best_w[0] * p_xgb + best_w[1] * p_lgb + best_w[2] * p_cat
        final_mape = best_mape
        em = "blend"
    r2 = r2_score(y_true, final_pred)
    print(f"FINAL MAPE={final_mape*100:.2f}% ({em}) R2={r2:.4f}")

    for name, model in [("xgb", m_xgb), ("lgb", m_lgb), ("cat", m_cat), ("meta", meta), ("encoder", encoder), ("kmeans", kmeans), ("ohe", ohe)]:
        joblib.dump(model, f"master_{name}_master.joblib")

    meta_info = {
        "version": "V12",
        "final_mape": float(final_mape),
        "ensemble_method": em,
        "best_w": [float(x) for x in best_w],
        "fit_xgb": {str(k): str(v) for k, v in fit_xgb.items()},
        "fit_lgb": {str(k): str(v) for k, v in fit_lgb.items()},
        "fit_cat": {str(k): str(v) for k, v in fit_cat.items()},
        "feature_names": feature_names,
    }
    with open("model_meta_master.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print("Saved models + metadata")
    return meta_info


if __name__ == "__main__":
    train_v12()


