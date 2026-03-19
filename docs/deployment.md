# Deployment Guide

This guide provides instructions for deploying trained sentiment analysis models from this project to various production environments.

## Model Types

The project includes two categories of models:

1. **Transformer Models** (BERT, RoBERTa, DeBERTa, etc.)
   - Higher accuracy (91-94%)
   - Larger size (50-520MB)
   - Slower inference (35-55ms on CPU)

2. **Classical ML Models** (XGBoost, LightGBM, etc.)
   - Faster inference (1-5ms on CPU)
   - Smaller size (<16MB)
   - Simpler deployment

## Exported Models

Best performing models are available in the `models/best_models/` directory with standardized structure:

```
models/best_models/
├── deberta-base_transformer/
│   ├── 20260319_123456/
│   ├── metadata.json
│   ├── model.pt (PyTorch format)
│   ├── model.onnx (ONNX format)
│   ├── tokenizer/
│   └── inference_example.py
```

Each model directory contains:
- `model.pt` or `model.pkl` - Trained model weights
- `tokenizer/` - HuggingFace tokenizer (for transformers)
- `config.json` - Model configuration
- `metadata.json` - Model metadata, MLflow run ID, metrics
- `inference_example.py` - Example inference code

## Options for Deployment

### Option 1: Local Inference (Fastest Setup)

Use the provided inference scripts directly:

```bash
# For transformer models
cd models/best_models/deberta-base_transformer/20260319_123456
python inference_example.py

# For classical models
cd models/best_models/xgboost_classical/20260319_123456
python inference_example.py
```

Modify the inference example script with your preprocessing pipeline.

### Option 2: ONNX Runtime (Optimized Performance)

Export to ONNX and use ONNX Runtime for faster inference:

```python
import onnxruntime as ort
import numpy as np

# Load ONNX model
session = ort.InferenceSession("models/best_models/deberta-base_transformer/latest/model.onnx")

# Prepare inputs
input_ids = tokenizer("Your text here", return_tensors="np", padding=True, truncation=True)

# Run inference
outputs = session.run(
    None,
    {
        "input_ids": input_ids["input_ids"].astype(np.int64),
        "attention_mask": input_ids["attention_mask"].astype(np.int64)
    }
)
logits = outputs[0]
```

**Advantages**: 2-3x faster than PyTorch on CPU, no PyTorch dependency

### Option 3: FastAPI/Flask API

Create a REST API for model serving:

```python
from fastapi import FastAPI
from transformers import AutoTokenizer
import torch

app = FastAPI()

# Load model and tokenizer
model_path = "models/best_models/deberta-base_transformer/latest"
model = torch.load(model_path + "/model.pt", map_location="cpu")
model.eval()
tokenizer = AutoTokenizer.from_pretrained(model_path + "/tokenizer")

@app.post("/predict")
async def predict(text: str):
    inputs = tokenizer(
        text,
        truncation=True,
        padding=True,
        max_length=512,
        return_tensors="pt"
    )
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        pred = torch.argmax(probs, dim=-1)
    
    return {
        "sentiment": "positive" if pred.item() == 1 else "negative",
        "confidence": probs[0][pred.item()].item(),
        "text": text
    }
```

Run with:
```bash
pip install fastapi uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Option 4: TorchServe (Production-Grade PyTorch Serving)

Use TorchServe for scalable PyTorch model serving:

```bash
# Install TorchServe
pip install torchserve torch-workflow-archiver

# Create mar file (model archive)
cd models/best_models/deberta-base_transformer/latest
torch-model-archiver \
  --model-name deberta-sentiment \
  --version 1.0 \
  --model-file inference_handler.py \
  --handler inference_handler.py \
  --runtime python \
  --export-path model_store

# Start TorchServe
torchserve --start --models deberta-sentiment.mar \
  --model-store model_store --ncs --ts 8080
```

### Option 5: TensorFlow Serving (with TF conversion)

NOTES:
- The transformer models are PyTorch-based
- You would need to convert to TensorFlow or use ONNX
- Not recommended unless you already have TF Serving infrastructure

### Option 6: SageMaker Endpoint (AWS)

```python
import boto3
from sagemaker.pytorch.model import PyTorchModel

# Create model
model = PyTorchModel(
    model_data="s3://bucket/models/deberta/model.tar.gz",
    role="SageMakerRole",
    entry_point="inference.py",
    framework_version="2.0.0",
    py_version="py310"
)

# Deploy
predictor = model.deploy(
    instance_type="ml.m5.xlarge",
    initial_instance_count=1,
    endpoint_name="sentiment-analysis"
)
```

### Option 7: Azure ML Endpoint

```python
from azureml.core import Workspace, Model
from azureml.core.webservice import AciWebservice

ws = Workspace.from_config()
model = Model.register(
    workspace=ws,
    model_path="models/best_models/deberta-base_transformer/latest",
    model_name="deberta-sentiment"
)

# Deploy to ACI
service = Model.deploy(
    ws,
    "sentiment-service",
    [model],
    inference_config=inference_config,
    deployment_config=AciWebservice.deploy_configuration(cpu_cores=1, memory_gb=4)
)
```

## Performance Optimization

### For Transformers:
- Use `torch.jit.script` or ONNX for 2-3x speedup
- Quantization: `torch.quantization.quantize_dynamic` or ONNX quantization
- Use half precision (FP16) if GPU available: `model.half()`
- Cache tokenizer results for repeated texts

### For Classical Models:
- Use `joblib` memory mapping for large models
- Vectorize batch predictions
- Pre-warm model in memory

## Monitoring

Track production metrics:

```python
import prometheus_client

# Create metrics
accuracy_gauge = prometheus_client.Gauge('model_accuracy', 'Current model accuracy')
latency_histogram = prometheus_client.Histogram('prediction_latency', 'Prediction latency')

@latency_histogram.time()
def predict_with_monitoring(text):
    result = predictor.predict(text)
    return result
```

## Cost Comparison (per 1M predictions)

| Deployment Option | Transformer (ms) | Classical (ms) | Hardware Cost |
|------------------|------------------|----------------|---------------|
| Local CPU        | 40-60ms          | 2-5ms          | $0 (existing) |
| AWS Lambda       | $0.20/1M req     | $0.20/1M req   | Pay per call  |
| SageMaker        | $0.0001/req      | $0.0001/req    | $0.10-$2/hr   |
| Azure ML         | $0.0001/req      | $0.0001/req    | $0.10-$2/hr   |
| GCP Vertex AI    | $0.0001/req      | $0.0001/req    | $0.10-$2/hr   |

**Recommendation**:
- Low volume (<100k/day): Local/FastAPI on existing server
- Medium volume (100k-1M/day): AWS Lambda or Cloud Run
- High volume: SageMaker/Vertex AI with autoscaling

## A/B Testing Strategy

Deploy multiple models and test:

```python
import random

models = {
    "deberta": deberta_predictor,
    "roberta": roberta_predictor,
    "xgboost": xgb_predictor
}

def ab_test_predict(text, traffic_split=None):
    """Route to different models based on traffic split."""
    if traffic_split is None:
        traffic_split = {"deberta": 0.5, "roberta": 0.3, "xgboost": 0.2}
    
    r = random.random()
    cumulative = 0
    for model_name, ratio in traffic_split.items():
        cumulative += ratio
        if r < cumulative:
            return models[model_name].predict(text), model_name
    
    return models["deberta"].predict(text), "deberta"
```

## Rollback Strategy

Keep previous model versions and switch instantly:

```python
# models/registry.json
{
  "current": "deberta-v2",
  "versions": {
    "deberta-v1": {"path": "...", "accuracy": 0.928},
    "deberta-v2": {"path": "...", "accuracy": 0.938},
    "xgb-v1": {"path": "...", "accuracy": 0.900}
  }
}

def predict_with_fallback(text, rollout_percentage=100):
    current_model = get_current_model()
    if random.random() < rollout_percentage / 100:
        return current_model.predict(text)
    else:
        # Fallback to previous stable version
        return get_fallback_model().predict(text)
```

## Security Considerations

1. **Input validation**: Sanitize texts to prevent injection attacks
2. **Rate limiting**: Limit API calls per user/IP
3. **Model encryption**: Encrypt model files at rest
4. **Access control**: Use API keys/OAuth for endpoints
5. **Audit logging**: Log all predictions for traceability
6. **Data privacy**: Do not log sensitive user text

## Scaling Guidelines

| QPS  | Recommendation                |
|------|-------------------------------|
| <10  | Single FastAPI instance      |
| 10-100 | Load balancer + 2-5 instances |
| 100-1000 | Autoscaling (K8s/Lambda)   |
| >1000 | Multiple regions + CDN cache |

## Troubleshooting

### Issue: Out of memory on GPU
```python
# Reduce batch size or use CPU
model.to('cpu')
# Or use gradient checkpointing for transformers
model.gradient_checkpointing_enable()
```

### Issue: Slow inference
- Check model is in eval mode: `model.eval()`
- Use ONNX Runtime instead of PyTorch
- Disable unnecessary features (e.g., return_dict=False)

### Issue: Model drift
- Monitor accuracy on a validation set
- Retrain periodically with new data
- Implement automated alerts on degradation

## Next Steps

1. Choose deployment option based on your requirements
2. Export required models: `python src/export.py`
3. Test locally: `python inference_example.py`
4. Deploy to staging environment
5. Load test and monitor
6. Production deployment with rollback plan

For any issues, check:
- Model artifact integrity: `python src/export.py --verify`
- Environment setup: `python verify_environment.py`
- MLflow tracking: `mlflow ui`
