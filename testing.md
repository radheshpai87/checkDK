🧠 Kubernetes Pod Failure Prediction API
========================================

This API predicts whether a Kubernetes pod will be **Healthy** or **Failure** using:

-   🌲 Random Forest

-   ⚡ XGBoost

-   🔁 LSTM

-   🏆 Ensemble Model

* * * * *

🚀 API Endpoints
----------------

```
POST /predict/random-forest
POST /predict/xgboost
POST /predict/lstm
POST /predict/ensemble

```

Base URL:

```
http://localhost:8000

```

* * * * *

🧪 Example API Usage
====================

* * * * *

1️⃣ Ensemble Prediction -- High Resource Usage (Failure Case)
------------------------------------------------------------

```
curl -X POST http://localhost:8000/predict/ensemble\
  -H "Content-Type: application/json"\
  -d '{
    "cpu_usage": 94.5,
    "memory_usage": 96.2,
    "disk_usage": 88.0,
    "network_latency": 45.0,
    "restart_count": 7,
    "probe_failures": 4,
    "node_cpu_pressure": 1,
    "node_memory_pressure": 1,
    "pod_age_minutes": 95
  }'

```

### Response

```
{
  "random_forest": {
    "model": "random_forest",
    "prediction": 1,
    "label": "failure",
    "confidence": 0.6168
  },
  "xgboost": {
    "model": "xgboost",
    "prediction": 1,
    "label": "failure",
    "confidence": 0.9983
  },
  "lstm": {
    "model": "lstm",
    "prediction": 1,
    "label": "failure",
    "confidence": 1.0
  },
  "ensemble_label": "failure",
  "ensemble_confidence": 0.8717
}

```

* * * * *

2️⃣ Ensemble Prediction -- Low Resource Usage (Healthy Case)
-----------------------------------------------------------

```
curl -X POST http://localhost:8000/predict/ensemble\
  -H "Content-Type: application/json"\
  -d '{
    "cpu_usage": 22.0,
    "memory_usage": 35.0,
    "disk_usage": 28.0,
    "network_latency": 5.0,
    "restart_count": 0,
    "probe_failures": 0,
    "node_cpu_pressure": 0,
    "node_memory_pressure": 0,
    "pod_age_minutes": 1440
  }'

```

### Response

```
{
  "random_forest": {
    "model": "random_forest",
    "prediction": 0,
    "label": "healthy",
    "confidence": 0.0
  },
  "xgboost": {
    "model": "xgboost",
    "prediction": 0,
    "label": "healthy",
    "confidence": 0.0
  },
  "lstm": {
    "model": "lstm",
    "prediction": 0,
    "label": "healthy",
    "confidence": 0.0
  },
  "ensemble_label": "healthy",
  "ensemble_confidence": 0.0
}

```

* * * * *

3️⃣ Random Forest -- Moderate Load (Healthy)
-------------------------------------------

```
curl -X POST http://localhost:8000/predict/random-forest\
  -H "Content-Type: application/json"\
  -d '{
    "cpu_usage": 58.0,
    "memory_usage": 62.0,
    "disk_usage": 50.0,
    "network_latency": 20.0,
    "restart_count": 4,
    "probe_failures": 2,
    "node_cpu_pressure": 1,
    "node_memory_pressure": 0,
    "pod_age_minutes": 300
  }'

```

### Response

```
{
  "model": "random_forest",
  "prediction": 0,
  "label": "healthy",
  "confidence": 0.0
}

```

* * * * *

4️⃣ Random Forest -- Gradual Increase in Failure Signals
-------------------------------------------------------

```
curl -X POST http://localhost:8000/predict/random-forest\
  -H "Content-Type: application/json"\
  -d '{
    "cpu_usage": 58.0,
    "memory_usage": 62.0,
    "disk_usage": 50.0,
    "network_latency": 20.0,
    "restart_count": 4,
    "probe_failures": 2,
    "node_cpu_pressure": 1,
    "node_memory_pressure": 1,
    "pod_age_minutes": 300
  }'

```

### Response

```
{
  "model": "random_forest",
  "prediction": 0,
  "label": "healthy",
  "confidence": 0.0245
}

```

* * * * *

5️⃣ Random Forest -- High CPU & Memory Pressure (Failure)
--------------------------------------------------------

```
curl -X POST http://localhost:8000/predict/random-forest\
  -H "Content-Type: application/json"\
  -d '{
    "cpu_usage": 93.0,
    "memory_usage": 91.0,
    "disk_usage": 50.0,
    "network_latency": 20.0,
    "restart_count": 4,
    "probe_failures": 2,
    "node_cpu_pressure": 1,
    "node_memory_pressure": 1,
    "pod_age_minutes": 300
  }'

```

### Response

```
{
  "model": "random_forest",
  "prediction": 1,
  "label": "failure",
  "confidence": 0.9236
}

```