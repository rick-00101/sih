from fastapi import APIRouter, Query

from services import demand_forecaster

router = APIRouter(prefix="/forecast/demand", tags=["demand"])


@router.get("")
def get_demand_forecast(
    hour: float = Query(..., ge=0, lt=24),
    temperature_c: float = Query(28.0, ge=-10, le=55),
    day_type: str = Query("weekday", pattern="^(weekday|weekend)$"),
):
    """
    DEMO/SIMULATED demand profile — deterministic (same inputs always give
    the same output), not randomized, and not a trained model, since no
    historical demand dataset exists for this prototype. See
    services/demand_forecaster.py.
    """
    return demand_forecaster.summary(hour, temperature_c, day_type)
