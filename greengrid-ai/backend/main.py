"""
GreenGrid AI — Phase 2 backend

Run with:
    cd backend
    pip install -r ../requirements.txt
    uvicorn main:app --reload --port 8000

Then open frontend/index.html in a browser (or serve it) — it will try
http://localhost:8000 automatically and fall back to its built-in
simulation if the backend isn't running, clearly labeling which is which.

Phase 2 adds: real weather (Open-Meteo), demand forecasting (deterministic
demo profile), a rule-based optimizer, a battery model, sustainability
calculations, threshold-based alerts, and a What-If simulation endpoint
that ties the real solar/wind ML models together with all of the above.
Phase 1's solar/wind prediction endpoints are unchanged.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import solar, wind, hydro, weather, demand, optimizer, sustainability, alerts, simulation
from schemas.prediction_schemas import HealthResponse
from services import solar_predictor, wind_predictor

app = FastAPI(
    title="GreenGrid AI — Phase 2 API",
    description="Real ML predictions for solar and wind (Phase 1) plus real weather, a rule-based "
                "optimizer, battery model, sustainability calculations, alerts, and a What-If "
                "simulation engine (Phase 2). Hydro remains a documented placeholder — see /predict/hydro.",
    version="2.0.0",
)

# Wide-open CORS: this is a hackathon demo backend meant to be called from a
# local static HTML file / localhost dev server, not a hardened production API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(solar.router)
app.include_router(wind.router)
app.include_router(hydro.router)
app.include_router(weather.router)
app.include_router(demand.router)
app.include_router(optimizer.router)
app.include_router(sustainability.router)
app.include_router(alerts.router)
app.include_router(simulation.router)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        solar_model_loaded=solar_predictor.is_loaded(),
        wind_model_loaded=wind_predictor.is_loaded(),
    )


@app.get("/")
def root():
    return {
        "service": "GreenGrid AI backend",
        "phase": 2,
        "endpoints": [
            "/health",
            "/predict/solar", "/predict/wind", "/predict/hydro (not implemented)",
            "/weather/current", "/weather/forecast",
            "/forecast/demand",
            "/optimize/run",
            "/sustainability/calculate",
            "/alerts/evaluate",
            "/simulation/run",
        ],
        "docs": "/docs",
    }
