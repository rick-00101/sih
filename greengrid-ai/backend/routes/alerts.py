from fastapi import APIRouter

from schemas.energy_schemas import AlertsRequest
from services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/evaluate")
def evaluate_alerts(payload: AlertsRequest):
    """
    Threshold-based alerts computed from the values you pass in — nothing
    is randomly generated, and nothing persists between calls (no alert
    history/database in Phase 2; see README limitations).
    """
    alerts = alert_service.evaluate_alerts(**payload.dict())
    return {"alerts": alerts, "source": "calculated"}
