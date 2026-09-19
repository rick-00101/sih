from fastapi import APIRouter, HTTPException

from schemas.prediction_schemas import WindPredictRequest, WindPredictResponse
from services import wind_predictor

router = APIRouter(prefix="/predict/wind", tags=["wind"])


@router.post("", response_model=WindPredictResponse)
def predict_wind(payload: WindPredictRequest):
    if not wind_predictor.is_loaded():
        raise HTTPException(
            status_code=503,
            detail=f"Wind model is not available: {wind_predictor.load_error()}",
        )
    try:
        power = wind_predictor.predict(
            wind_speed=payload.wind_speed,
            wind_direction=payload.wind_direction,
            theoretical_power=payload.theoretical_power,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc

    return WindPredictResponse(
        predicted_power=round(power, 2),
        model=wind_predictor.metadata().get("selected_model", "unknown"),
    )
