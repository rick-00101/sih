# GreenGrid AI — Phase 1 + Phase 2

AI-powered renewable energy management platform — SIH 2026, Navodaya Innovation Team.

Phase 1 replaced the fully-simulated prototype's solar and wind numbers with **real datasets and real trained ML models**. Phase 2 adds **real live weather**, a **rule-based optimizer**, a **battery model**, **sustainability calculations**, **threshold-based alerts**, and a **What-If Simulation engine** that ties the real ML models together with all of the above — following PREDICT → OPTIMIZE → ACT. The frontend UI/visual design is unchanged from Phase 1 in both phases; only backend integration was added.

## Architecture

```
Kaggle datasets (solar, wind)                    Open-Meteo (live weather)
        │                                                │
        ▼                                                ▼
  ml/*/train.py  →  backend/models/*/model.joblib   backend/services/weather_service.py
        │                                                │
        └──────────────────┬─────────────────────────────┘
                            ▼
                    backend/main.py (FastAPI)
        /health  /predict/solar  /predict/wind  /predict/hydro (501)
        /weather/current  /weather/forecast
        /forecast/demand
        /optimize/run
        /sustainability/calculate
        /alerts/evaluate
        /simulation/run   ← ties solar+wind ML, demand, optimizer, battery,
                             sustainability, and alerts together in one call
                            │
                            ▼
                frontend/index.html (existing GreenGrid UI, unchanged)
       Overview: live weather header + "Phase 1 real model check" card
       Simulation Lab: "Run simulation on backend" button + results panel
       All other pages: still the original Phase 1 client-side simulation,
       clearly labeled as such (not yet wired to Phase 2 endpoints)
```

## How to run it

**1. Install dependencies**
```
pip install -r requirements.txt
```

**2. (Optional) Configure**
```
cp .env.example .env
# edit LATITUDE/LONGITUDE for your location, battery size, emission factor, etc.
```
Every value has a working default — this step can be skipped for a quick demo.

**3. (Already done, but to reproduce) Train the models**
```
cd ml/solar && python3 train.py && cd ../wind && python3 train.py
```

**4. Run the backend**
```
cd backend
uvicorn main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for interactive API docs (all Phase 1 + Phase 2 endpoints).

**5. Open the frontend**
```
cd frontend
python3 -m http.server 8080
```
Open `http://localhost:8080`. On the **Overview** page: a live weather header (needs internet access to Open-Meteo) and the Phase 1 "real model check" card. On the **Simulation Lab** page: pick a scenario, then click **"Run simulation on backend"** to see the real solar/wind models + optimizer + sustainability calculation run end-to-end for that scenario.

**6. Run the tests**
```
python3 tests/test_pipeline.py   # Phase 1: data, preprocessing, models — 18 checks
python3 tests/test_phase2.py     # Phase 2: demand, battery, optimizer, sustainability, alerts, wind curve, irradiance — 24 checks
python3 tests/test_api.py        # requires the backend running — 12 checks
```
54/54 pass as of this build.

## Data sources

| Source | Dataset | Size |
|---|---|---|
| Solar | [Kaggle: Solar Power Generation Data](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data) (anikannal) — 2 plants, 22 inverters each | 15 May – 17 Jun 2020, 15-min resolution, 6,416 rows after merging generation + weather |
| Wind | [Kaggle: Wind Turbine SCADA Dataset](https://www.kaggle.com/datasets/berkerisen/wind-turbine-scada-dataset) (berkerisen), `T1.csv` | Full year 2018, 10-min resolution, 50,530 rows |
| Weather | [Open-Meteo](https://open-meteo.com) forecast API | Live, no API key required |

## Phase 1 — ML models

### Solar
- **Target:** total plant `AC_POWER` (kW). **Features:** `IRRADIATION`, `AMBIENT_TEMPERATURE`, `MODULE_TEMPERATURE`, `hour_sin`, `hour_cos`, `is_plant_2`.
- **Excluded (leakage):** `DC_POWER`, `DAILY_YIELD`, `TOTAL_YIELD`.
- **Split:** chronological 70/15/15 per plant. **Result:** Random Forest selected.

| Model | MAE (kW) | RMSE (kW) | R² |
|---|---|---|---|
| Linear Regression (baseline) | 1405.7 | 2182.2 | 0.905 |
| **Random Forest (selected)** | **501.2** | **1352.3** | **0.964** |

### Wind
- **Target:** `LV ActivePower` (kW). **Features:** `wind_speed`, `theoretical_power`, `dir_sin`, `dir_cos`.
- **Split:** chronological 70/15/15 across the full year. **Result:** Linear Regression selected — honestly, not forced (see explanation in code comments: `theoretical_power` already captures the curve's non-linearity, and the Random Forest overfit to within-year patterns).

| Model | MAE (kW) | RMSE (kW) | R² |
|---|---|---|---|
| **Linear Regression (selected)** | **254.1** | **462.9** | **0.888** |
| Random Forest | 325.8 | 667.8 | 0.767 |

## Phase 2 — new components

- **Weather service** (`services/weather_service.py`) — real Open-Meteo data, with timeout/connection/malformed-response handling. Returns `{"available": false, "error": "..."}` on failure rather than inventing numbers.
- **Demand forecaster** (`services/demand_forecaster.py`) — deterministic demo profile (no historical demand dataset exists for this prototype). Same inputs always produce the same output. Clearly labeled `simulated_demo_profile`.
- **Battery model** (`services/battery_service.py`) — SOC only changes from actual computed energy allocation, never randomly. Configurable capacity, efficiency, min/max SOC, max charge/discharge power.
- **Optimizer** (`services/optimizer.py`) — rule-based allocation (surplus → charge/export/curtail; deficit → discharge/grid import), each decision paired with a plain-English reason. Deliberately not over-engineered with a solver library for this prototype (see Phase 3 below for the OR-Tools upgrade path).
- **Sustainability** (`services/sustainability_service.py`) — deterministic "GreenGrid operational score" (explicitly labeled as this project's own composite indicator, not a certified environmental rating) and a CO₂-avoided estimate with the assumption always stated alongside the number.
- **Alerts** (`services/alert_service.py`) — threshold-based, not random. Includes a maintenance-style anomaly flag, but only when an independent expected-vs-actual reading is supplied — see the honesty note in `routes/simulation.py` about why the simulation path deliberately does NOT trigger that flag from clear-sky-vs-cloudy comparisons of the same model (that would mislabel a weather effect as an equipment fault).
- **Simulation engine** (`routes/simulation.py`) — the What-If Simulation Lab's backend: takes scenario inputs (cloud cover, temperature, wind speed, battery SOC, hour), estimates irradiance, calls the real solar and wind models, gets a demand estimate, runs the optimizer, and calculates sustainability + alerts — all in one deterministic call.
- **Wind/solar scale note:** both trained models are utility/plant-scale (tens of thousands of kW). For the Simulation Lab and optimizer to work against a small building's demand (a few kW), their output is scaled down by a configurable `SOLAR_SCALE_FACTOR` / `WIND_SCALE_FACTOR` (default 0.001) — the raw model output is always included alongside the scaled figure in API responses so this is never hidden.
- **Wind forecast input:** at forecast time we don't have the Kaggle turbine's actual `Theoretical_Power_Curve` reading, so `services/wind_power_curve.py` approximates it from wind speed using a standard cubic turbine curve (documented as a generic approximation, not the exact manufacturer curve).

## API endpoints

| Endpoint | Method | Type |
|---|---|---|
| `/health` | GET | status |
| `/predict/solar` | POST | ML prediction |
| `/predict/wind` | POST | ML prediction |
| `/predict/hydro` | POST | **501 Not Implemented** (honest placeholder) |
| `/weather/current`, `/weather/forecast` | GET | real API data |
| `/forecast/demand` | GET | simulated demo profile |
| `/optimize/run` | POST | calculated |
| `/sustainability/calculate` | POST | calculated |
| `/alerts/evaluate` | POST | calculated |
| `/simulation/run` | POST | combines ML prediction + simulated + calculated (see response's `source_summary` field) |

## Data labeling — what's real, predicted, calculated, or simulated

Every value returned by the backend carries a `source` field (or an equivalent note) set to one of:
- `live_api` — real weather from Open-Meteo
- `ml_prediction` — output of one of the two trained models
- `calculated` — a deterministic formula (battery physics, optimizer allocation, CO₂/GreenScore)
- `simulated_demo_profile` — the demand curve (no real demand dataset exists yet)

The frontend surfaces this in two places currently: the Overview weather header (real, or an honest "unavailable" message) and the Simulation Lab's backend results panel (shows the `source_summary` string directly). The rest of the dashboard (battery/flow animation, other pages' numbers) still runs on the original Phase 1 client-side simulation and is not yet re-labeled per-value — see Known Limitations.

## Environment variables

See `.env.example` — location, weather API URL/timeout, grid emission factor, battery parameters, reference turbine curve constants, and the solar/wind demo scale factors. All optional; sane defaults are baked into `backend/config.py`.

## Testing

- `tests/test_pipeline.py` — Phase 1 offline checks (data, preprocessing, model loading, prediction sanity) — 18 checks
- `tests/test_phase2.py` — Phase 2 offline checks (demand, battery, optimizer's surplus/deficit/full-battery/low-battery cases, sustainability, alerts, wind curve, irradiance) — 24 checks
- `tests/test_api.py` — live API checks against a running backend, including the honest 501 on `/predict/hydro` and 422 validation errors — 12 checks

**Note on weather testing:** this development environment's network sandbox could not reach `api.open-meteo.com` (outbound request returned HTTP 403 from the sandbox's own egress proxy, not from Open-Meteo). This actually verified the *failure path* — `/weather/current` correctly returned `{"available": false, "error": "..."}` instead of crashing or inventing data. The success path (real weather returned) has NOT been verified in this environment and should be checked once running with normal internet access.

## Known limitations (honest, as of this build)

- **Hydro and biogas** — not implemented. `services/hydro_placeholder.py` documents the intended Phase 2/3 approach (Open-Meteo Flood API + `P = ρ·g·Q·H·η` physics formula) but nothing is wired up.
- **No database / no history** — alerts, simulation runs, and predictions are all computed fresh per request; nothing persists between calls. Acceptable for a hackathon prototype per the project's own "don't over-engineer" instruction.
- **Weather → solar/wind auto-feed is not wired** — `/weather/current` and `/simulation/run` both exist and both work, but the simulation endpoint currently takes weather-like values as direct input rather than automatically pulling them from the live weather endpoint. Connecting them is straightforward (the weather response's `cloud_cover_pct`, `temperature_c`, and `wind_speed_kmh` map directly onto `SimulationRequest`'s fields) but wasn't done here to keep the scope reviewable.
- **Most dashboard pages are not yet repointed to Phase 2 endpoints** — only the Overview weather header and the Simulation Lab's new results panel call the Phase 2 backend live. AI Forecast, Smart Optimizer, Load Scheduler, Predictive Maintenance, Sustainability, and Alerts pages still show the original Phase 1 client-side simulation, which remains clearly labeled as simulated from Phase 1's work — none of it was changed to claim to be more real than it is, but it also hasn't been upgraded yet.
- **Optimizer is rule-based, not a solver** — deliberately, per the spec's own "do not overengineer" instruction. An OR-Tools linear/MILP formulation is a natural Phase 3 upgrade once there are more constraints worth optimizing jointly (e.g. multiple flexible loads with real deadlines).
- **GreenScore weights and the solar/wind scale factors are this project's own design choices** — configurable, and documented as such in the code and API responses, not derived from any external standard.

## Phase 3 recommendations

1. Wire the remaining dashboard pages (AI Forecast, Smart Optimizer, Load Scheduler, Sustainability, Alerts) to the Phase 2 endpoints the same way the Simulation Lab now is.
2. Auto-feed `/simulation/run` from `/weather/current` instead of requiring manual weather-like inputs.
3. Implement the hydro physics calculation for real using the Open-Meteo Flood API (`services/hydro_placeholder.py` already documents the formula).
4. Add a small persistence layer (SQLite is enough) so alerts and simulation runs have history instead of being stateless per-request.
5. Upgrade the optimizer to OR-Tools once the Load Scheduler's flexible-load list needs to be optimized jointly with battery/grid decisions (multi-appliance scheduling is a genuine combinatorial problem; the current rule-based optimizer handles single-step allocation well but doesn't do multi-hour appliance scheduling).
6. Train an actual anomaly-detection model (Isolation Forest) once a real, independent sensor feed exists to compare against the model's expectation — see the honesty note in `routes/simulation.py` about why this isn't done yet.

