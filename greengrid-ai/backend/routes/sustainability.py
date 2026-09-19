from fastapi import APIRouter

from schemas.energy_schemas import SustainabilityRequest
from services import sustainability_service

router = APIRouter(prefix="/sustainability", tags=["sustainability"])


@router.post("/calculate")
def calculate_sustainability(payload: SustainabilityRequest):
    """
    Deterministic GreenGrid operational score + CO2-avoided estimate.
    Not a certified environmental rating — see the "label" and
    "assumption" fields in the response for the exact method used.
    """
    co2 = sustainability_service.co2_avoided_kg(payload.renewable_used_kwh)
    score = sustainability_service.green_score(
        renewable_utilization_pct=payload.renewable_utilization_pct,
        grid_dependency_pct=payload.grid_dependency_pct,
        battery_utilization_pct=payload.battery_utilization_pct,
        curtailment_pct=payload.curtailment_pct,
    )
    return {"co2": co2, "green_score": score}
