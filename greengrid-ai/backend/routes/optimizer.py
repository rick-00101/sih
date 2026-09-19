from fastapi import APIRouter

from schemas.energy_schemas import OptimizeRequest, OptimizeResponse
from services import optimizer

router = APIRouter(prefix="/optimize", tags=["optimizer"])


@router.post("/run", response_model=OptimizeResponse)
def run_optimizer(payload: OptimizeRequest):
    """
    Rule-based allocation of renewable generation, battery, and grid to
    meet demand. Deterministic — same inputs always give the same
    allocation and the same explanation.
    """
    result = optimizer.optimize(
        renewable_generation_kw=payload.renewable_generation_kw,
        demand_kw=payload.demand_kw,
        battery_soc_pct=payload.battery_soc_pct,
        allow_export=payload.allow_export,
        duration_hours=payload.duration_hours,
    )
    return OptimizeResponse(**result.__dict__)
