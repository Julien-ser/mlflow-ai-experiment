"""
Comprehensive MLFlow Experiment Tracking

This module provides centralized utilities for managing MLFlow experiments,
including:
- Creating/getting experiments for different model families
- Setting standardized tags (model_type, dataset_version, preprocessing_config)
- Logging model artifacts and predictions
- Managing artifact storage structure
"""

import mlflow
from mlflow.entities import Experiment
from pathlib import Path
from typing import Dict, Optional, Any
import pandas as pd
import joblib


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    import yaml  # type: ignore

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def setup_mlflow_tracking(tracking_uri: str = "sqlite:///mlflow.db") -> None:
    """Configure MLflow tracking URI."""
    mlflow.set_tracking_uri(tracking_uri)
    print(f"✓ MLflow tracking URI set to: {tracking_uri}")


def get_or_create_family_experiment(config: dict, model_family: str) -> Experiment:
    """
    Get or create experiment for a specific model family.

    Args:
        config: Configuration dictionary with 'experiments' mapping
        model_family: Model family ('classical' or 'transformers')

    Returns:
        MLflow Experiment object
    """
    family_experiments = config.get("experiments", {})
    if not family_experiments:
        raise ValueError("No experiments configured in config['experiments']")
    if model_family not in family_experiments:
        raise ValueError(
            f"Unknown model family: {model_family}. "
            f"Available families: {list(family_experiments.keys())}"
        )

    experiment_name = family_experiments[model_family]
    artifact_location = config["experiment"].get("artifact_location", "mlartifacts")

    # Try to get existing experiment
    experiment = mlflow.get_experiment_by_name(experiment_name)

    if experiment is None:
        # Create new experiment with base tags from config
        base_tags = config["experiment"].get("tags", {})
        experiment_id = mlflow.create_experiment(
            name=experiment_name,
            artifact_location=artifact_location,
            tags=base_tags,
        )
        experiment = mlflow.get_experiment(experiment_id)
        print(f"✓ Created experiment: {experiment_name} (ID: {experiment_id})")
    else:
        print(f"✓ Using existing experiment: {experiment_name}")

    return experiment


def set_standard_tags(
    run: mlflow.ActiveRun,
    model_type: str,
    dataset_version: str,
    preprocessing_config: str,
    framework: Optional[str] = None,
    **extra_tags: Any,
) -> None:
    """
    Set standardized tags on an MLflow run.

    Args:
        run: Active MLflow run
        model_type: Type of model (e.g., 'bert', 'logistic_regression')
        dataset_version: Version string for the dataset
        preprocessing_config: Name of preprocessing configuration used
        framework: Framework name (e.g., 'sklearn', 'transformers', 'xgboost')
        **extra_tags: Additional custom tags to set
    """
    tags = {
        "model_type": model_type,
        "dataset_version": dataset_version,
        "preprocessing_config": preprocessing_config,
    }
    if framework:
        tags["framework"] = framework

    tags.update(extra_tags)

    for key, value in tags.items():
        mlflow.set_tag(key, value)


def log_sklearn_model(
    model: Any,
    artifact_path: str = "model",
    input_example: Optional[Any] = None,
) -> None:
    """Log a scikit-learn model to MLflow."""
    import mlflow.sklearn as mlflow_sklearn

    if input_example is not None:
        mlflow_sklearn.log_model(
            model, artifact_path=artifact_path, input_example=input_example
        )
    else:
        mlflow_sklearn.log_model(model, artifact_path=artifact_path)


def log_transformers_model(
    model: Any,
    tokenizer: Any,
    artifact_path: str = "model",
    task: str = "text-classification",
    input_example: Optional[str] = None,
) -> None:
    """Log a transformer model (with tokenizer) to MLflow."""
    from mlflow.transformers import log_model as mlflow_transformers_log_model

    if input_example is None:
        input_example = "Sample text for classification"

    mlflow_transformers_log_model(
        transformers_model=model,
        tokenizer=tokenizer,
        artifact_path=artifact_path,
        task=task,
        input_example=input_example,
    )


def log_model_artifact(
    model: Any,
    model_type: str,
    framework: str,
    artifact_path: str = "model",
    **kwargs: Any,
) -> None:
    """
    Log a model artifact using the appropriate MLflow flavor.

    Args:
        model: The trained model object
        model_type: Type of model (e.g., 'logistic_regression', 'bert')
        framework: Framework identifier ('sklearn', 'transformers', 'xgboost')
        artifact_path: Relative path within the run's artifacts
        **kwargs: Additional arguments passed to the specific log function
    """
    if framework == "sklearn":
        log_sklearn_model(model, artifact_path=artifact_path, **kwargs)
    elif framework == "transformers":
        # Expects kwargs to include tokenizer
        log_transformers_model(model, artifact_path=artifact_path, **kwargs)
    elif framework == "xgboost":
        # XGBoost is also handled by sklearn flavor
        log_sklearn_model(model, artifact_path=artifact_path, **kwargs)
    else:
        # Fallback: save as pickle
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "model.pkl"
            joblib.dump(model, path)
            mlflow.log_artifact(str(path), artifact_path=artifact_path)


def log_predictions(
    predictions_df: pd.DataFrame,
    artifact_path: str = "predictions",
    filename: str = "predictions.csv",
) -> None:
    """
    Log predictions DataFrame as a CSV artifact.

    Args:
        predictions_df: DataFrame containing predictions
        artifact_path: Directory within artifacts to store the file
        filename: Name of the CSV file
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / filename
        predictions_df.to_csv(path, index=False)
        mlflow.log_artifact(str(path), artifact_path=artifact_path)


def create_experiment_tracker(
    config_path: str = "config.yaml",
) -> Dict[str, Any]:
    """
    Initialize experiment tracking and return utilities.

    Returns:
        Dictionary with experiment utilities:
        - 'config': loaded configuration
        - 'tracking_uri': current tracking URI
        - 'experiments': mapping of model families to experiment names
    """
    config = load_config(config_path)

    # Setup tracking
    tracking_uri = config["tracking"]["uri"]
    setup_mlflow_tracking(tracking_uri)

    # Print available experiments
    experiments = config.get("experiments", {})
    print("Available model family experiments:")
    for family, name in experiments.items():
        print(f"  {family}: {name}")

    return {
        "config": config,
        "tracking_uri": tracking_uri,
        "experiments": experiments,
    }
