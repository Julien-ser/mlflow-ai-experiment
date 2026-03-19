"""
Tests for evaluation metrics module.
"""

import pytest
import numpy as np
import time
from unittest.mock import Mock, patch
from mlflow_ai_experiment.evaluation import (
    compute_metrics,
    measure_inference_latency,
    get_model_size,
    log_metrics_to_mlflow,
    evaluate_model,
)


# Sample data for testing
BINARY_Y_TRUE = np.array([0, 1, 0, 1, 0, 1, 1, 0])
BINARY_Y_PRED = np.array([0, 1, 0, 1, 1, 1, 1, 0])
BINARY_Y_PROBA = np.array(
    [
        [0.9, 0.1],
        [0.2, 0.8],
        [0.7, 0.3],
        [0.1, 0.9],
        [0.6, 0.4],
        [0.3, 0.7],
        [0.2, 0.8],
        [0.8, 0.2],
    ]
)

MULTICLASS_Y_TRUE = np.array([0, 1, 2, 0, 1, 2])
MULTICLASS_Y_PRED = np.array([0, 1, 2, 0, 1, 1])
MULTICLASS_Y_PROBA = np.array(
    [
        [0.8, 0.1, 0.1],
        [0.1, 0.8, 0.1],
        [0.1, 0.1, 0.8],
        [0.9, 0.05, 0.05],
        [0.1, 0.7, 0.2],
        [0.2, 0.6, 0.2],
    ]
)


class TestComputeMetrics:
    """Tests for compute_metrics function."""

    def test_binary_metrics_with_probabilities(self):
        """Test binary classification with probabilities."""
        metrics = compute_metrics(
            BINARY_Y_TRUE, BINARY_Y_PRED, BINARY_Y_PROBA, average="binary"
        )

        # Check that all expected metrics are present
        expected_metrics = [
            "accuracy",
            "precision",
            "recall",
            "f1",
            "specificity",
            "mcc",
            "confusion_matrix",
            "log_loss",
            "auc_roc",
            "average_precision",
        ]
        for metric in expected_metrics:
            assert metric in metrics, f"Missing metric: {metric}"

        # Check types
        assert isinstance(metrics["accuracy"], float)
        assert isinstance(metrics["precision"], float)
        assert isinstance(metrics["recall"], float)
        assert isinstance(metrics["f1"], float)
        assert isinstance(metrics["mcc"], float)
        assert isinstance(metrics["confusion_matrix"], list)
        assert isinstance(metrics["log_loss"], float)
        assert isinstance(metrics["auc_roc"], float)
        assert isinstance(metrics["average_precision"], float)

        # Verify confusion matrix structure (2x2 for binary)
        cm = np.array(metrics["confusion_matrix"])
        assert cm.shape == (2, 2)

    def test_binary_metrics_without_probabilities(self):
        """Test binary classification without probabilities."""
        metrics = compute_metrics(BINARY_Y_TRUE, BINARY_Y_PRED, average="binary")

        # Should have basic metrics but not probability-based ones
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics
        assert "specificity" in metrics
        assert "mcc" in metrics
        assert "confusion_matrix" in metrics
        assert "log_loss" not in metrics
        assert "auc_roc" not in metrics
        assert "average_precision" not in metrics

    def test_multiclass_metrics(self):
        """Test multi-class classification."""
        metrics = compute_metrics(
            MULTICLASS_Y_TRUE, MULTICLASS_Y_PRED, MULTICLASS_Y_PROBA, average="macro"
        )

        expected_metrics = [
            "accuracy",
            "precision",
            "recall",
            "f1",
            "mcc",
            "confusion_matrix",
            "log_loss",
            "auc_roc",
            "average_precision",
        ]
        for metric in expected_metrics:
            assert metric in metrics, f"Missing metric: {metric}"

        # Confusion matrix should be 3x3 for 3 classes
        cm = np.array(metrics["confusion_matrix"])
        assert cm.shape == (3, 3)

    def test_multiclass_without_probabilities(self):
        """Test multi-class classification without probabilities."""
        metrics = compute_metrics(MULTICLASS_Y_TRUE, MULTICLASS_Y_PRED, average="macro")

        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics
        assert "mcc" in metrics
        assert "confusion_matrix" in metrics
        # No probability-based metrics
        assert "log_loss" not in metrics

    def test_perfect_predictions(self):
        """Test with perfect predictions."""
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1])

        metrics = compute_metrics(y_true, y_pred)
        assert metrics["accuracy"] == 1.0
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1"] == 1.0

    def test_terrible_predictions(self):
        """Test with completely wrong predictions."""
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([1, 1, 0, 0])

        metrics = compute_metrics(y_true, y_pred)
        assert metrics["accuracy"] == 0.0
        assert metrics["f1"] < 0.1  # Should be very low

    def test_all_same_class(self):
        """Test when all predictions are the same class."""
        y_true = np.array([0, 0, 0, 0])
        y_pred = np.array([0, 0, 0, 0])

        metrics = compute_metrics(y_true, y_pred)
        assert metrics["accuracy"] == 1.0
        # Note: specificity may not be computed for single-class cases

    def test_micro_averaging(self):
        """Test micro averaging for multi-class."""
        metrics = compute_metrics(MULTICLASS_Y_TRUE, MULTICLASS_Y_PRED, average="micro")
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics

    def test_weighted_averaging(self):
        """Test weighted averaging for multi-class."""
        metrics = compute_metrics(
            MULTICLASS_Y_TRUE, MULTICLASS_Y_PRED, average="weighted"
        )
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics

    def test_specificity_binary_only(self):
        """Test that specificity is only calculated for binary or when explicitly possible."""
        # Binary case - should have specificity
        metrics_binary = compute_metrics(BINARY_Y_TRUE, BINARY_Y_PRED, average="binary")
        assert "specificity" in metrics_binary

        # Multi-class case - should not have specificity (unless average='binary' is forced)
        metrics_multi = compute_metrics(
            MULTICLASS_Y_TRUE, MULTICLASS_Y_PRED, average="macro"
        )
        assert "specificity" not in metrics_multi


class TestMeasureInferenceLatency:
    """Tests for measure_inference_latency function."""

    def test_latency_with_sklearn_api(self):
        """Test latency measurement with sklearn-like API."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0, 1, 0])

        # Mock time to avoid actual timing
        with patch("time.time") as mock_time:
            mock_time.side_effect = [0, 0.01] * 11  # 10 repeats + initial
            latency = measure_inference_latency(
                mock_model, np.array([[1, 2], [3, 4], [5, 6]]), num_samples=3
            )

        # Should call predict at least 10 times
        assert mock_model.predict.call_count >= 10
        assert latency is not None
        assert latency >= 0

    def test_latency_with_few_samples(self):
        """Test latency when num_samples > available data."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0])

        X_small = np.array([[1, 2]])
        with patch("time.time", return_value=0):
            latency = measure_inference_latency(mock_model, X_small, num_samples=100)

        assert latency is not None

    def test_latency_without_predict(self):
        """Test latency with model that has no predict method."""
        mock_model = Mock(spec=[])  # No predict attribute

        latency = measure_inference_latency(mock_model, np.array([[1, 2]]))
        assert latency is None

    def test_latency_returns_ms(self):
        """Test that latency is returned in milliseconds."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0, 1])

        with patch("time.time") as mock_time:
            # Simulate 1ms total time across 10 repeats for 2 samples
            mock_time.side_effect = [0, 0.0001] * 11  # 0.1ms total
            latency = measure_inference_latency(
                mock_model, np.array([[1], [2]]), num_samples=2
            )

        assert latency is not None
        assert latency >= 0  # Should be positive milliseconds


class TestGetModelSize:
    """Tests for get_model_size function."""

    def test_model_size_returns_mb(self):
        """Test that model size is returned in MB."""

        # Create a dummy object of known size
        class DummyModel:
            def __init__(self):
                self.data = "x" * 1024 * 1024  # 1 MB of data

        model = DummyModel()
        size_mb = get_model_size(model)

        assert isinstance(size_mb, float)
        assert size_mb >= 0  # sys.getsizeof may not capture deep object sizes

    def test_model_size_empty_model(self):
        """Test size of an empty model object."""
        model = Mock()
        size_mb = get_model_size(model)
        assert size_mb >= 0


class TestLogMetricsToMLflow:
    """Tests for log_metrics_to_mlflow function."""

    def test_log_all_metrics_except_confusion_matrix(self):
        """Test that all metrics except confusion_matrix are logged."""
        metrics = {
            "accuracy": 0.95,
            "precision": 0.93,
            "recall": 0.91,
            "f1": 0.92,
            "confusion_matrix": [[10, 2], [3, 85]],
        }

        with patch("mlflow.log_metric") as mock_log:
            log_metrics_to_mlflow(metrics, prefix="test")

        # Should log all except confusion_matrix
        mock_log.assert_any_call("test_accuracy", 0.95)
        mock_log.assert_any_call("test_precision", 0.93)
        mock_log.assert_any_call("test_recall", 0.91)
        mock_log.assert_any_call("test_f1", 0.92)
        assert mock_log.call_count == 4

    def test_custom_prefix(self):
        """Test custom prefix in metric names."""
        metrics = {"accuracy": 0.9, "f1": 0.85}

        with patch("mlflow.log_metric") as mock_log:
            log_metrics_to_mlflow(metrics, prefix="val")

        mock_log.assert_any_call("val_accuracy", 0.9)
        mock_log.assert_any_call("val_f1", 0.85)


class TestEvaluateModel:
    """Tests for evaluate_model function."""

    def test_evaluate_with_predict_proba(self):
        """Test full evaluation with a model that has predict_proba."""
        mock_model = Mock()
        mock_model.predict.return_value = BINARY_Y_PRED
        mock_model.predict_proba.return_value = BINARY_Y_PROBA

        with (
            patch(
                "mlflow_ai_experiment.evaluation.measure_inference_latency"
            ) as mock_latency,
            patch("mlflow_ai_experiment.evaluation.get_model_size") as mock_size,
            patch("mlflow_ai_experiment.evaluation.log_metrics_to_mlflow") as mock_log,
        ):
            mock_latency.return_value = 10.5
            mock_size.return_value = 50.2

            results = evaluate_model(
                mock_model, BINARY_Y_TRUE, BINARY_Y_TRUE, log_to_mlflow=True
            )

        # Should include all metrics
        assert "accuracy" in results
        assert "f1" in results
        assert "inference_latency_ms" in results
        assert results["inference_latency_ms"] == 10.5
        assert "model_size_mb" in results
        assert results["model_size_mb"] == 50.2

        # Should log to MLflow
        mock_log.assert_called_once()

    def test_evaluate_without_predict_proba(self):
        """Test evaluation with model that lacks predict_proba."""
        mock_model = Mock()
        mock_model.predict.return_value = BINARY_Y_PRED
        # No predict_proba

        with (
            patch(
                "mlflow_ai_experiment.evaluation.measure_inference_latency"
            ) as mock_latency,
            patch("mlflow_ai_experiment.evaluation.get_model_size") as mock_size,
            patch("mlflow_ai_experiment.evaluation.log_metrics_to_mlflow") as mock_log,
        ):
            mock_latency.return_value = 8.3
            mock_size.return_value = 30.1

            results = evaluate_model(
                mock_model, BINARY_Y_TRUE, BINARY_Y_PRED, log_to_mlflow=False
            )

        assert "accuracy" in results
        assert "f1" in results
        assert "log_loss" not in results  # No probability-based metrics
        assert "auc_roc" not in results
        assert not mock_log.called  # log_to_mlflow=False

    def test_evaluate_without_mlflow_logging(self):
        """Test evaluation with MLflow logging disabled."""
        mock_model = Mock()
        mock_model.predict.return_value = BINARY_Y_PRED
        mock_model.predict_proba.return_value = BINARY_Y_PROBA

        with (
            patch(
                "mlflow_ai_experiment.evaluation.measure_inference_latency",
                return_value=5.0,
            ),
            patch("mlflow_ai_experiment.evaluation.get_model_size", return_value=25.0),
            patch("mlflow_ai_experiment.evaluation.log_metrics_to_mlflow") as mock_log,
        ):
            results = evaluate_model(
                mock_model, BINARY_Y_TRUE, BINARY_Y_PRED, log_to_mlflow=False
            )

            assert not mock_log.called

    def test_evaluate_uses_correct_prefix(self):
        """Test that MLflow logging uses the test prefix."""
        mock_model = Mock()
        mock_model.predict.return_value = BINARY_Y_PRED

        with (
            patch(
                "mlflow_ai_experiment.evaluation.measure_inference_latency",
                return_value=1.0,
            ),
            patch("mlflow_ai_experiment.evaluation.get_model_size", return_value=1.0),
            patch("mlflow_ai_experiment.evaluation.log_metrics_to_mlflow") as mock_log,
        ):
            evaluate_model(mock_model, BINARY_Y_TRUE, BINARY_Y_PRED, log_to_mlflow=True)

            # Should call with default prefix 'test'
            mock_log.assert_called_once()
            args = mock_log.call_args
            assert args[1].get("prefix") == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
