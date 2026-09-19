"""
GreenGrid AI — Weather service (Phase 2)

Calls Open-Meteo (https://open-meteo.com), a free weather API that needs
no API key. This is REAL, live weather data — not simulated.

Handles: timeouts, connection failures, and malformed responses, always
returning a structured result with `available: False` on failure rather
than raising, so a weather outage degrades the dashboard gracefully
instead of crashing it.
"""
import requests
from datetime import datetime, timezone

import config

# WMO weather codes -> short human label (Open-Meteo uses the WMO standard)
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def _condition_label(code):
    return WMO_CODES.get(code, "Unknown")


def get_current_and_forecast(latitude: float = None, longitude: float = None) -> dict:
    """
    Returns a dict with:
      available (bool)
      current: {temperature_c, apparent_temperature_c, cloud_cover_pct,
                 precipitation_mm, precipitation_probability_pct, wind_speed_kmh,
                 wind_direction_deg, condition, updated_at}
      hourly: list of up to 24 {time, temperature_c, cloud_cover_pct,
                 precipitation_probability_pct, shortwave_radiation, wind_speed_kmh}
      error: str (only present when available is False)
    """
    lat = latitude if latitude is not None else config.LATITUDE
    lon = longitude if longitude is not None else config.LONGITUDE

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,cloud_cover,precipitation,"
                    "weather_code,wind_speed_10m,wind_direction_10m",
        "hourly": "temperature_2m,cloud_cover,precipitation_probability,"
                  "shortwave_radiation,wind_speed_10m,wind_direction_10m",
        "forecast_days": 2,
        "timezone": "auto",
    }

    try:
        resp = requests.get(config.WEATHER_API_BASE_URL, params=params, timeout=config.WEATHER_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return {"available": False, "error": "Weather API request timed out"}
    except requests.exceptions.ConnectionError:
        return {"available": False, "error": "Could not reach the weather API (no network / DNS failure)"}
    except requests.exceptions.HTTPError as exc:
        return {"available": False, "error": f"Weather API returned an error: {exc}"}
    except (ValueError, KeyError) as exc:
        return {"available": False, "error": f"Weather API returned an unexpected response: {exc}"}

    try:
        cur = data["current"]
        current_out = {
            "temperature_c": cur["temperature_2m"],
            "apparent_temperature_c": cur.get("apparent_temperature"),
            "cloud_cover_pct": cur["cloud_cover"],
            "precipitation_mm": cur.get("precipitation", 0.0),
            "wind_speed_kmh": cur["wind_speed_10m"],
            "wind_direction_deg": cur["wind_direction_10m"],
            "condition": _condition_label(cur.get("weather_code")),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        # Match "precipitation probability right now" to the closest hourly slot.
        precip_prob_now = None
        if times:
            precip_probs = hourly.get("precipitation_probability", [])
            if precip_probs:
                precip_prob_now = precip_probs[0]
        current_out["precipitation_probability_pct"] = precip_prob_now

        hourly_out = []
        for i in range(min(24, len(times))):
            hourly_out.append({
                "time": times[i],
                "temperature_c": hourly.get("temperature_2m", [None]*len(times))[i],
                "cloud_cover_pct": hourly.get("cloud_cover", [None]*len(times))[i],
                "precipitation_probability_pct": hourly.get("precipitation_probability", [None]*len(times))[i],
                "shortwave_radiation_wm2": hourly.get("shortwave_radiation", [None]*len(times))[i],
                "wind_speed_kmh": hourly.get("wind_speed_10m", [None]*len(times))[i],
            })

        return {"available": True, "current": current_out, "hourly": hourly_out}
    except (KeyError, IndexError) as exc:
        return {"available": False, "error": f"Weather API response was missing expected fields: {exc}"}
