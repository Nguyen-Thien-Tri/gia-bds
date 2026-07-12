"""
FastAPI Application - House Price Prediction API
Deploy target: Google Cloud Run
"""
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from prediction import load_models, predict_price

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App Initialisation ──────────────────────────────────
app = FastAPI(
    title="House Price Prediction API",
    description="Predict Vietnamese real estate prices using XGBoost + LightGBM ensemble",
    version="1.0.0",
)

# ── Models (lazy-loaded on first request) ───────────────
_model_xgb = None
_model_lgb = None
_encoder = None


def get_models():
    global _model_xgb, _model_lgb, _encoder
    if _model_xgb is None:
        logger.info("Loading ML models...")
        _model_xgb, _model_lgb, _encoder = load_models()
        logger.info("Models loaded successfully.")
    return _model_xgb, _model_lgb, _encoder


# ── Request Schema ──────────────────────────────────────
class PropertyInput(BaseModel):
    Loại_BĐS: str = Field(..., alias="Loại BĐS", examples=["nhà riêng"])
    Quận: str = Field(..., examples=["Đống Đa"])
    Phường_Xã_Thị_trấn: str = Field("", alias="Phường Xã Thị trấn", examples=["Phường Láng Hạ"])
    Diện_tích: float = Field(..., alias="Diện tích", gt=0, examples=[50.0])
    Tọa_độ_x: float = Field(..., alias="Tọa độ x", examples=[21.015])
    Tọa_độ_y: float = Field(..., alias="Tọa độ y", examples=[105.815])
    Số_tầng: Optional[float] = Field(None, alias="Số tầng", examples=[4])
    Số_phòng_ngủ: Optional[float] = Field(None, alias="Số phòng ngủ", examples=[3])
    Mặt_tiền: Optional[float] = Field(None, alias="Mặt tiền", examples=[4.0])
    Đường_vào: Optional[float] = Field(None, alias="Đường vào", examples=[3.0])
    Mô_tả: Optional[str] = Field("", alias="Mô tả", examples=["Nhà đẹp phố Láng Hạ, ô tô vào nhà, kinh doanh tốt, nở hậu."])

    class Config:
        # Allow both underscored and Vietnamese-named fields
        populate_by_name = True


class PriceResponse(BaseModel):
    price_vnd: float = Field(..., description="Predicted price in VND")
    price_billion: float = Field(..., description="Predicted price in billions VND")
    currency: str = "VND"


# ── Health Check ────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint for Cloud Run."""
    return {"status": "ok", "service": "house-price-prediction"}


# ── Prediction Endpoint ─────────────────────────────────
@app.post("/predict", response_model=PriceResponse, tags=["Prediction"])
async def predict(input_data: PropertyInput):
    """
    Predict house price based on property information.
    
    Returns the predicted price in both VND and billions VND.
    """
    try:
        models = get_models()
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise HTTPException(status_code=503, detail="Model not available")

    # Convert Pydantic model → dict with original Vietnamese keys
    raw = input_data.model_dump(by_alias=True)
    # Alias-free keys for the prediction module
    property_data = {
        "Loại BĐS": raw["Loại BĐS"],
        "Quận": raw["Quận"],
        "Phường Xã Thị trấn": raw["Phường Xã Thị trấn"],
        "Diện tích": raw["Diện tích"],
        "Tọa độ x": raw["Tọa độ x"],
        "Tọa độ y": raw["Tọa độ y"],
        "Số tầng": raw.get("Số tầng", 0) or 0,
        "Số phòng ngủ": raw.get("Số phòng ngủ", 0) or 0,
        "Mặt tiền": raw.get("Mặt tiền", 0) or 0,
        "Đường vào": raw.get("Đường vào", 0) or 0,
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
        "message": "House Price Prediction API",
        "docs": "/docs",
        "health": "/health",
    }