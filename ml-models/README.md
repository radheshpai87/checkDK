# Pod Failure Detection – ML Models

ML models that detect impending failure in Docker containers and Kubernetes pods
by analysing real-time resource and health metrics.

---

## Dataset

`datasets/pod_failure_dataset.csv` – 50 000 labelled pod observations.

| Feature               | Description                              |
|-----------------------|------------------------------------------|
| `cpu_usage`           | CPU usage % (0-100)                      |
| `memory_usage`        | Memory usage % (0-100)                   |
| `disk_usage`          | Disk usage % (0-100)                     |
| `network_latency`     | Network latency (ms)                     |
| `restart_count`       | Number of container restarts             |
| `probe_failures`      | Liveness / readiness probe failures      |
| `node_cpu_pressure`   | Node under CPU pressure (0 / 1)          |
| `node_memory_pressure`| Node under memory pressure (0 / 1)       |
| `pod_age_minutes`     | Pod age in minutes                       |
| `failure_label`       | **Target** – 0 = healthy, 1 = failure    |

---

## Models

| Model         | Location                       | Framework      |
|---------------|--------------------------------|----------------|
| Random Forest | `models/random_forest/`        | scikit-learn   |
| XGBoost       | `models/xgboost_model/`        | XGBoost        |
| LSTM          | `models/lstm_model/`           | PyTorch        |

Each model directory contains:
- `train.py`   – trains the model and saves artefacts to disk
- `predict.py` – inference helper class used by the API

---

## Quick Start (Docker – recommended)

### 1. Train all models

```bash
docker compose run --rm train
```

This trains Random Forest, XGBoost, and LSTM sequentially and writes the
serialised model files into `models/*/` on your host via volume mounts.

### 2. Start the inference API

```bash
docker compose up api
```

The API will be available at **http://localhost:8000**.
Interactive Swagger docs: **http://localhost:8000/docs**

---

## Quick Start (local Python)

```bash
# Install dependencies
pip install -r requirements.txt

# Train all models
python train_all.py

# Start the API
uvicorn api.app:app --reload
```

---

## API Reference

### `GET /health`

Returns which models are currently loaded.

```json
{
  "status": "ok",
  "loaded_models": ["random_forest", "xgboost", "lstm"]
}
```

### `POST /predict/random-forest`
### `POST /predict/xgboost`
### `POST /predict/lstm`

Run a single-model prediction.

**Request body:**
```json
{
  "cpu_usage": 91.5,
  "memory_usage": 93.0,
  "disk_usage": 45.0,
  "network_latency": 34.0,
  "restart_count": 5,
  "probe_failures": 3,
  "node_cpu_pressure": 1,
  "node_memory_pressure": 1,
  "pod_age_minutes": 120
}
```

**Response:**
```json
{
  "model": "random_forest",
  "prediction": 1,
  "label": "failure",
  "confidence": 0.91
}
```

### `POST /predict/ensemble`

Runs all loaded models and returns a majority-vote result.

**Response:**
```json
{
  "random_forest": { "model": "random_forest", "prediction": 1, "label": "failure", "confidence": 0.91 },
  "xgboost":       { "model": "xgboost",       "prediction": 1, "label": "failure", "confidence": 0.88 },
  "lstm":          { "model": "lstm",           "prediction": 1, "label": "failure", "confidence": 0.84 },
  "ensemble_label": "failure",
  "ensemble_confidence": 0.876
}
```

---

## Project Structure

```
ml-models/
├── datasets/
│   └── pod_failure_dataset.csv
├── models/
│   ├── random_forest/
│   │   ├── train.py
│   │   ├── predict.py
│   │   ├── rf_model.pkl       # generated after training
│   │   └── scaler.pkl         # generated after training
│   ├── xgboost_model/
│   │   ├── train.py
│   │   ├── predict.py
│   │   ├── xgb_model.pkl      # generated after training
│   │   └── scaler.pkl         # generated after training
│   └── lstm_model/
│       ├── train.py
│       ├── predict.py
│       ├── lstm_model.pt      # generated after training
│       └── scaler.pkl         # generated after training
├── api/
│   ├── app.py                 # FastAPI application
│   └── schemas.py             # Pydantic request/response schemas
├── train_all.py               # Trains all three models in sequence
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```
