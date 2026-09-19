from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/predict/hydro", tags=["hydro"])


@router.post("")
def predict_hydro():
    """
    Not implemented in Phase 1.

    Hydro is intentionally left unimplemented here — there is no reliable
    historical hydro generation dataset to train on, and no live API is
    wired up yet. See backend/services/hydro_placeholder.py for the
    documented Phase 2 plan (Open-Meteo Flood API + physics formula).
    Returning a fake number here would violate the project's own
    honesty rule, so this endpoint reports itself as not implemented
    instead.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "Hydro prediction is not implemented in Phase 1. "
            "Planned for Phase 2: live river discharge from the Open-Meteo "
            "Flood API, combined with a physics formula (P = rho * g * Q * H * eta), "
            "not a trained ML model. See services/hydro_placeholder.py."
        ),
    )
