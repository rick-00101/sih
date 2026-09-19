from fastapi import APIRouter, Query
from typing import Optional

import config
from services import weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/current")
def current_weather(latitude: Optional[float] = Query(None), longitude: Optional[float] = Query(None)):
    """
    Real, live weather data from Open-Meteo (no API key required).
    On failure, returns {"available": false, "error": "..."} with HTTP 200 —
    a weather outage is a normal, expected condition for the frontend to
    handle gracefully, not a server error.
    """
    result = weather_service.get_current_and_forecast(latitude, longitude)
    result["location"] = {
        "latitude": latitude if latitude is not None else config.LATITUDE,
        "longitude": longitude if longitude is not None else config.LONGITUDE,
    }
    result["source"] = "live_api"
    return result


@router.get("/forecast")
def weather_forecast(latitude: Optional[float] = Query(None), longitude: Optional[float] = Query(None)):
    """Same underlying call as /current, but the response is framed around the hourly array."""
    result = weather_service.get_current_and_forecast(latitude, longitude)
    result["source"] = "live_api"
    return result
