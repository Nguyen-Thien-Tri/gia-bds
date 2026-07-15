"""
FastAPI Application - House Price Prediction API V11
Deploy target: Google Cloud Run
"""
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from prediction import load_models, predict_price

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App Initialisation ──────────────────────────────────
app = FastAPI(
    title="House Price Prediction API",
    description="Predict Vietnamese real estate prices using XGBoost + LightGBM ensemble (V11)",
    version="1.1.0",
)

# ── Models (lazy-loaded on first request) ───────────────
_model_xgb = None
_model_lgb = None
_encoder = None
_kmeans = None
_meta = None


def get_models():
    global _model_xgb, _model_lgb, _encoder, _kmeans, _meta
    if _model_xgb is None:
        logger.info("Loading ML models (V11)...")
        _model_xgb, _model_lgb, _encoder, _kmeans, _meta = load_models()
        logger.info(
            "Models loaded successfully. V11 | MAPE: %s | XGB weight: %.2f",
            _meta.get("mape", "N/A"),
            _meta.get("xgb_weight", 0.7),
        )
    return _model_xgb, _model_lgb, _encoder, _kmeans, _meta


# ── Request Schema ──────────────────────────────────────
class PropertyInput(BaseModel):
    # ── Core fields ──────────────────────────────────────
    Loại_BĐS: str = Field(..., alias="Loại BĐS", examples=["nhà riêng"])
    Quận: str = Field(..., examples=["Đống Đa"])
    Địa_chỉ_1: str = Field("", alias="Địa chỉ 1", examples=["Phường Láng Hạ"])
    Diện_tích: float = Field(..., alias="Diện tích", gt=0, examples=[50.0])
    Tọa_độ_x: float = Field(..., alias="Tọa độ x", examples=[21.015])
    Tọa_độ_y: float = Field(..., alias="Tọa độ y", examples=[105.815])

    # ── Optional numeric fields ──────────────────────────
    Số_tầng: Optional[float] = Field(None, alias="Số tầng", examples=[4])
    Số_phòng_ngủ: Optional[float] = Field(None, alias="Số phòng ngủ", examples=[3])
    Số_phòng_tắm_vệ_sinh: Optional[float] = Field(None, alias="Số phòng tắm - vệ sinh", examples=[2])
    Mặt_tiền: Optional[float] = Field(None, alias="Mặt tiền", examples=[4.0])
    Đường_vào: Optional[float] = Field(None, alias="Đường vào", examples=[3.0])

    # ── Optional categorical fields ──────────────────────
    Hướng_nhà: Optional[str] = Field(None, alias="Hướng nhà", examples=["Đông"])
    Hướng_ban_công: Optional[str] = Field(None, alias="Hướng ban công", examples=["Tây Nam"])
    Pháp_lý: Optional[str] = Field(None, alias="Pháp lý", examples=["Sổ đỏ"])
    Nội_thất: Optional[str] = Field(None, alias="Nội thất", examples=["Đầy đủ"])
    Căn_góc: Optional[str] = Field("Không", alias="Căn góc", examples=["Có"])

    # ── Description text ─────────────────────────────────
    Mô_tả: Optional[str] = Field("", alias="Mô tả", examples=["Nhà đẹp phố Láng Hạ, ô tô vào nhà, kinh doanh tốt, nở hậu."])

    class Config:
        populate_by_name = True


class PriceResponse(BaseModel):
    price_vnd: float = Field(..., description="Predicted price in VND")
    price_billion: float = Field(..., description="Predicted price in billions VND")
    currency: str = "VND"


# ── Health Check ────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint for Cloud Run."""
    return {"status": "ok", "service": "house-price-prediction-v11"}


# ── Prediction Endpoint ─────────────────────────────────
@app.post("/predict", response_model=PriceResponse, tags=["Prediction"])
async def predict(input_data: PropertyInput):
    """
    Predict house price based on property information (V11).

    Returns the predicted price in both VND and billions VND.
    """
    try:
        models = get_models()
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise HTTPException(status_code=503, detail="Model not available")

    # Convert Pydantic model → dict with original Vietnamese keys
    raw = input_data.model_dump(by_alias=True)

    property_data = {
        "Loại BĐS": raw["Loại BĐS"],
        "Quận": raw["Quận"],
        "Địa chỉ 1": raw.get("Địa chỉ 1", ""),
        "Diện tích": raw["Diện tích"],
        "Tọa độ x": raw["Tọa độ x"],
        "Tọa độ y": raw["Tọa độ y"],
        "Số tầng": raw.get("Số tầng", 0) or 0,
        "Số phòng ngủ": raw.get("Số phòng ngủ", 0) or 0,
        "Số phòng tắm - vệ sinh": raw.get("Số phòng tắm - vệ sinh", 0) or 0,
        "Mặt tiền": raw.get("Mặt tiền", 0) or 0,
        "Đường vào": raw.get("Đường vào", 0) or 0,
        "Hướng nhà": raw.get("Hướng nhà", ""),
        "Hướng ban công": raw.get("Hướng ban công", ""),
        "Pháp lý": raw.get("Pháp lý", ""),
        "Nội thất": raw.get("Nội thất", ""),
        "Căn góc": raw.get("Căn góc", "Không"),
        "Mô tả": raw.get("Mô tả", "") or "",
    }

    try:
        price = predict_price(property_data, *models)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    return PriceResponse(
        price_vnd=round(price, 0),
        price_billion=round(price / 1e9, 2),
    )


# ── Root ─────────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "message": "House Price Prediction API V11",
        "docs": "/docs",
        "health": "/health",
    }