from pydantic import BaseModel, Field


class SolarPredictRequest(BaseModel):
    irradiation: float = Field(..., ge=0, le=1.5, description="Solar irradiation (kW/m^2), typically 0-1.2")
    ambient_temperature: float = Field(..., ge=-10, le=60, description="Ambient air temperature (deg C)")
    module_temperature: float = Field(..., ge=-10, le=90, description="Solar panel module temperature (deg C)")
    hour: float = Field(..., ge=0, lt=24, description="Hour of day, 0-23.99 (e.g. 13.5 = 1:30 PM)")
    plant_id: int = Field(1, description="1 or 2 — which reference plant's pattern to use (this dataset only has two)")


class SolarPredictResponse(BaseModel):
    predicted_power: float
    unit: str = "kW"
    model: str
    source: str = "ml_prediction"


class WindPredictRequest(BaseModel):
    wind_speed: float = Field(..., ge=0, le=40, description="Wind speed (m/s)")
    wind_direction: float = Field(..., ge=0, lt=360, description="Wind direction (degrees, 0-359)")
    theoretical_power: float = Field(..., ge=0, le=4000, description="Manufacturer theoretical power for this wind speed (kW), from the turbine's power curve")


class WindPredictResponse(BaseModel):
    predicted_power: float
    unit: str = "kW"
    model: str
    source: str = "ml_prediction"


class HealthResponse(BaseModel):
    status: str
    solar_model_loaded: bool
    wind_model_loaded: bool
