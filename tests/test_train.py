"""
Integration tests for MLflow experiment tracking.
"""

import os
import pytest
import mlflow
import pandas as pd
from mlflow_ai_experiment.experiment_tracker import (
    get_or_create_family_experiment,
    set_standard_tags,
    log_predictions,
    log_model_artifact,
)


@pytest.fixture(scope="function")
def temp_mlflow_db(tmp_path):
    """Create a temporary MLflow tracking database."""
    db_path = tmp_path / "mlflow.db"
    tracking_uri = f"sqlite:///{db_path}"
    original_uri = mlflow.get_tracking_uri()
    # Store original env vars to restore later
    orig_exp_id = os.environ.get("MLFLOW_EXPERIMENT_ID")
    orig_exp_name = os.environ.get("MLFLOW_EXPERIMENT_NAME")
    # Clear MLflow experiment env vars to avoid contamination
    os.environ.pop("MLFLOW_EXPERIMENT_ID", None)
    os.environ.pop("MLFLOW_EXPERIMENT_NAME", None)
    mlflow.set_tracking_uri(tracking_uri)
    # Reset the tracking client and clear cached experiment ID
    mlflow.tracking._tracking_service.client = None
    mlflow.tracking.fluent._active_experiment_id = None
    yield tracking_uri
    # Restore original tracking URI and clear caches
    mlflow.set_tracking_uri(original_uri)
    mlflow.tracking._tracking_service.client = None
    mlflow.tracking.fluent._active_experiment_id = None
    # Restore original env vars
    if orig_exp_id is not None:
        os.environ["MLFLOW_EXPERIMENT_ID"] = orig_exp_id
    if orig_exp_name is not None:
        os.environ["MLFLOW_EXPERIMENT_NAME"] = orig_exp_name
    try:
        db_path.unlink()
    except Exception:
        pass


def test_set_standard_tags(temp_mlflow_db):
    with mlflow.start_run() as run:
        set_standard_tags(
            model_type="test_model",
            dataset_version="v0.1",
            preprocessing_config="test_preproc",
            framework="test_framework",
            custom_tag="custom_value",
        )
        run_data = mlflow.get_run(run.info.run_id)
        tags = run_data.data.tags
        assert tags["model_type"] == "test_model"
        assert tags["dataset_version"] == "v0.1"
        assert tags["preprocessing_config"] == "test_preproc"
        assert tags["framework"] == "test_framework"
        assert tags["custom_tag"] == "custom_value"


def test_get_or_create_family_experiment(temp_mlflow_db, tmp_path):
    artifact_loc = str(tmp_path / "artifacts")
    config = {
        "experiments": {
            "classical": "test_classical_exp",
        },
        "experiment": {"artifact_location": artifact_loc, "tags": {"team": "ml"}},
    }
    exp = get_or_create_family_experiment(config, "classical")
    assert exp.name == "test_classical_exp"
    exp_info = mlflow.get_experiment(exp.experiment_id)
    assert exp_info.tags.get("team") == "ml"
    exp2 = get_or_create_family_experiment(config, "classical")
    assert exp2.experiment_id == exp.experiment_id
    with pytest.raises(ValueError):
        get_or_create_family_experiment(config, "unknown")


def test_log_predictions(temp_mlflow_db):
    df = pd.DataFrame({"input": [1, 2, 3], "prediction": [0, 1, 0]})
    with mlflow.start_run() as run:
        log_predictions(df, artifact_path="predictions", filename="preds.csv")
        run_id = run.info.run_id
    # After run ends, check artifact
    client = mlflow.MlflowClient()
    try:
        files = client.list_artifacts(run_id, path="predictions")
        assert any(f.path == "predictions/preds.csv" for f in files)
    except Exception as e:
        pytest.fail(f"Failed to find predictions artifact: {e}")


def test_log_model_artifact_sklearn(temp_mlflow_db):
    from sklearn.linear_model import LogisticRegression
    import numpy as np

    X = np.array([[0], [1]])
    y = np.array([0, 1])
    model = LogisticRegression().fit(X, y)
    with mlflow.start_run() as run:
        log_model_artifact(
            model,
            model_type="logistic_regression",
            framework="sklearn",
            artifact_path="model",
        )
        run_id = run.info.run_id
    # After run ends, check artifact
    client = mlflow.MlflowClient()
    try:
        files = client.list_artifacts(run_id, path="model")
        assert any("MLmodel" in f.path for f in files)
    except Exception as e:
        pytest.fail(f"Failed to find model artifact: {e}")
