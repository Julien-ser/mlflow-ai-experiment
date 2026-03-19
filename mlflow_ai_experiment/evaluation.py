"""
Comprehensive evaluation metrics for classification models.

This module provides a unified interface for evaluating both classical ML
and transformer models, with support for:
- Standard metrics: accuracy, precision, recall, F1, specificity, MCC
- Advanced metrics: AUC-ROC, log loss, confusion matrix
- Performance metrics: inference latency, memory footprint
- MLflow logging with consistent naming
- Cross-validation support
"""

import time
import psutil
import mlflow
import numpy as np
from typing import Any, Dict, Optional, Tuple, List
from sklearn.metrics import (  # type: ignore
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    log_loss,
    matthews_corrcoef,
    recall_score,
    average_precision_score,
)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    average: str = "binary",
) -> Dict[str, Any]:
    """
    Compute comprehensive evaluation metrics for classification.

    Args:
        y_true: True labels (array-like)
        y_pred: Predicted labels (array-like)
        y_proba: Prediction probabilities (array-like, shape=(n_samples, n_classes))
        average: Averaging method for multi-class ('binary', 'macro', 'micro', 'weighted')

    Returns:
        Dictionary with all computed metrics
    """
    metrics: Dict[str, Any] = {}

    # Basic metrics
    metrics["accuracy"] = float(accuracy_score(y_true, y_pred))
    metrics["precision"] = float(
        precision_score(y_true, y_pred, average=average, zero_division="warn")
    )
    metrics["recall"] = float(
        recall_score(y_true, y_pred, average=average, zero_division="warn")
    )
    metrics["f1"] = float(
        f1_score(y_true, y_pred, average=average, zero_division="warn")
    )

    # Specificity (true negative rate) - only for binary
    if average == "binary" or len(np.unique(y_true)) == 2:
        cm = confusion_matrix(y_true, y_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            metrics["specificity"] = float(specificity)

    # Matthews Correlation Coefficient
    metrics["mcc"] = float(matthews_corrcoef(y_true, y_pred))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    metrics["confusion_matrix"] = cm.tolist()

    # Probability-based metrics (if available)
    if y_proba is not None:
        try:
            # Log loss (cross-entropy)
            metrics["log_loss"] = float(log_loss(y_true, y_proba))

            # AUC-ROC (binary case or one-vs-rest for multi-class)
            n_classes = y_proba.shape[1] if y_proba.ndim > 1 else 2
            if n_classes == 2:
                # For binary, use probability of positive class
                if y_proba.ndim > 1:
                    y_proba_pos = y_proba[:, 1]
                else:
                    y_proba_pos = y_proba
                metrics["auc_roc"] = float(roc_auc_score(y_true, y_proba_pos))
            else:
                # Multi-class: use one-vs-rest
                metrics["auc_roc"] = float(
                    roc_auc_score(y_true, y_proba, multi_class="ovr", average=average)
                )

            # Average Precision (AP)
            if n_classes == 2:
                if y_proba.ndim > 1:
                    y_proba_pos = y_proba[:, 1]
                else:
                    y_proba_pos = y_proba
                metrics["average_precision"] = float(
                    average_precision_score(y_true, y_proba_pos)
                )
            else:
                metrics["average_precision"] = float(
                    average_precision_score(y_true, y_proba, average=average)
                )

        except Exception as e:
            # Some metrics may fail for various reasons (e.g., only one class present)
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
            model.predict(X_test)
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
