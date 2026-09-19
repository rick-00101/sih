from typing import Optional, List
from pydantic import BaseModel, Field


class DemandForecastRequest(BaseModel):
    hour: float = Field(..., ge=0, lt=24)
    temperature_c: float = Field(28.0, ge=-10, le=55)
    day_type: str = Field("weekday", pattern="^(weekday|weekend)$")


class OptimizeRequest(BaseModel):
    renewable_generation_kw: float = Field(..., ge=0)
    demand_kw: float = Field(..., ge=0)
    battery_soc_pct: float = Field(..., ge=0, le=100)
    allow_export: bool = True
    duration_hours: float = Field(1 / 6, gt=0, le=24)


class OptimizeResponse(BaseModel):
    renewable_generation_kw: float
    demand_kw: float
    renewable_used_kw: float
    battery_charging_kw: float
    battery_discharging_kw: float
    grid_import_kw: float
    grid_export_kw: float
    curtailed_kw: float
    battery_soc_pct: float
    recommended_action: str
    reason: str
    source: str = "calculated"


class SustainabilityRequest(BaseModel):
    renewable_used_kwh: float = Field(..., ge=0)
    renewable_utilization_pct: float = Field(..., ge=0, le=100)
    grid_dependency_pct: float = Field(..., ge=0, le=100)
    battery_utilization_pct: float = Field(0.0, ge=0, le=100)
    curtailment_pct: float = Field(0.0, ge=0, le=100)


class AlertsRequest(BaseModel):
    battery_soc_pct: float = Field(..., ge=0, le=100)
    renewable_generation_kw: float = Field(..., ge=0)
    demand_kw: float = Field(..., ge=0)
    cloud_cover_pct: Optional[float] = Field(None, ge=0, le=100)
    precipitation_probability_pct: Optional[float] = Field(None, ge=0, le=100)
    grid_import_kw: float = Field(0.0, ge=0)
    curtailed_kw: float = Field(0.0, ge=0)
    solar_expected_kw: Optional[float] = Field(None, ge=0)
    solar_actual_kw: Optional[float] = Field(None, ge=0)


class SimulationRequest(BaseModel):
    """Every field is an override with a realistic default, so the caller
    only needs to set the ones they're experimenting with."""
    hour: float = Field(13.0, ge=0, lt=24)
    cloud_cover_pct: float = Field(15.0, ge=0, le=100)
    precipitation_probability_pct: float = Field(10.0, ge=0, le=100)
    ambient_temperature_c: float = Field(30.0, ge=-10, le=55)
    wind_speed_ms: float = Field(6.0, ge=0, le=40)
    battery_soc_pct: float = Field(70.0, ge=0, le=100)
    day_type: str = Field("weekday", pattern="^(weekday|weekend)$")
    allow_export: bool = True
    plant_id: int = Field(1, ge=1, le=2)
