from fastapi import APIRouter, HTTPException

from schemas.prediction_schemas import SolarPredictRequest, SolarPredictResponse
from services import solar_predictor

router = APIRouter(prefix="/predict/solar", tags=["solar"])


@router.post("", response_model=SolarPredictResponse)
def predict_solar(payload: SolarPredictRequest):
    if not solar_predictor.is_loaded():
        raise HTTPException(
            status_code=503,
            detail=f"Solar model is not available: {solar_predictor.load_error()}",
        )
    try:
        power = solar_predictor.predict(
            irradiation=payload.irradiation,
            ambient_temperature=payload.ambient_temperature,
            module_temperature=payload.module_temperature,
            hour=payload.hour,
            plant_id=payload.plant_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc

    return SolarPredictResponse(
        predicted_power=round(power, 2),
        model=solar_predictor.metadata().get("selected_model", "unknown"),
    )
