"""
Evaluation metrics for classification models.
"""

import time
import psutil  # type: ignore
import numpy as np
from sklearn.metrics import (  # type: ignore
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
import mlflow


def compute_metrics(y_true, y_pred, y_proba=None):
    """
    Compute comprehensive evaluation metrics.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_proba: Prediction probabilities (optional)

    Returns:
        Dictionary with all metrics
    """
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average="binary"),
        "recall": recall_score(y_true, y_pred, average="binary"),
        "f1": f1_score(y_true, y_pred, average="binary"),
    }

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    metrics["confusion_matrix"] = cm.tolist()

    # Additional metrics if probabilities available
    if y_proba is not None:
        # Log loss (cross-entropy)
        from sklearn.metrics import log_loss

        try:
            metrics["log_loss"] = log_loss(y_true, y_proba)
        except Exception:
            pass

    return metrics


def measure_inference_latency(model, X, num_samples=100):
    """
    Measure inference latency for a model.

    Returns:
        Average latency in milliseconds
    """
    if hasattr(model, "predict"):
        # Use sklearn-like API
        X_test = X[:num_samples] if len(X) > num_samples else X

        start = time.time()
        for _ in range(10):  # Repeat to get stable average
            predictions = model.predict(X_test)
        end = time.time()

        avg_latency = ((end - start) / (10 * len(X_test))) * 1000
        return avg_latency
    else:
        # Custom predict interface
        return None


def get_model_size(model):
    """Get approximate model size in MB."""
    import sys

    size_bytes = sys.getsizeof(model)
    return size_bytes / (1024 * 1024)  # Convert to MB


def log_metrics_to_mlflow(metrics, prefix="val"):
    """
    Log metrics to MLFlow.

    Args:
        metrics: Dictionary of metrics
        prefix: Prefix for metric names (e.g., 'val', 'test')
    """
    for key, value in metrics.items():
        if key != "confusion_matrix":
            mlflow.log_metric(f"{prefix}_{key}", value)


def evaluate_model(model, X_test, y_test, log_to_mlflow=True):
    """
    Complete model evaluation pipeline.

    Returns:
        Dictionary with all evaluation results
    """
    # Make predictions
    y_pred = model.predict(X_test)

    # Get probabilities if available
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)
        results = compute_metrics(y_test, y_pred, y_proba)
    else:
        results = compute_metrics(y_test, y_pred)

    # Measure latency
    latency_ms = measure_inference_latency(model, X_test)
    if latency_ms:
        results["inference_latency_ms"] = latency_ms

    # Get model size
    results["model_size_mb"] = get_model_size(model)

    if log_to_mlflow:
        log_metrics_to_mlflow(results, prefix="test")

    return results
