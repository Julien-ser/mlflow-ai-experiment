#!/usr/bin/env python3
"""
MLFlow Tracking Setup Script
Initializes MLflow tracking infrastructure for the experiment tracking project.
"""

import yaml  # type: ignore
import mlflow
from mlflow.entities import Experiment  # type: ignore
from pathlib import Path
from typing import Optional


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def setup_mlflow_tracking(config: dict) -> None:
    """Configure MLflow tracking URI and initialize experiment."""

    # Set tracking URI (local directory)
    tracking_uri = config["tracking"]["uri"]
    mlflow.set_tracking_uri(tracking_uri)

    print(f"✓ MLflow tracking URI set to: {tracking_uri}")

    # Create mlruns directory if it doesn't exist
    if tracking_uri.startswith("file:"):
        mlruns_path = tracking_uri.replace("file:", "")
        Path(mlruns_path).mkdir(exist_ok=True)
        print(f"✓ MLruns directory ready: {mlruns_path}")


def get_or_create_experiment(
    config: dict, experiment_name: Optional[str] = None
) -> "Experiment":
    """
    Get existing experiment or create new one.

    Args:
        config: Configuration dictionary
        experiment_name: Optional experiment name. If not provided, uses the default from config.

    Returns:
        MLflow Experiment object
    """
    if experiment_name is None:
        experiment_name = config["experiment"]["name"]
        if not isinstance(experiment_name, str):
            raise ValueError("Experiment name must be a string")

    artifact_location = config["experiment"].get("artifact_location", "mlruns")

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
        print(f"✓ Created new experiment: {experiment_name} (ID: {experiment_id})")
    else:
        print(
            f"✓ Using existing experiment: {experiment_name} (ID: {experiment.experiment_id})"
        )

    return experiment


def get_or_create_family_experiment(config: dict, model_family: str) -> "Experiment":
    """
    Get or create experiment for a specific model family.

    Args:
        config: Configuration dictionary
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
            f"Available families in config: {list(family_experiments.keys())}"
        )

    experiment_name = family_experiments[model_family]
    return get_or_create_experiment(config, experiment_name)


def initialize_mlflow() -> "Experiment":
    """
    Initialize MLflow tracking and return the experiment object.

    Returns:
        MLflow Experiment object
    """
    config = load_config()
    setup_mlflow_tracking(config)
    experiment = get_or_create_experiment(config)

    print("\n✓ MLflow initialization complete!")
    print(f"  - Tracking URI: {mlflow.get_tracking_uri()}")
    print(f"  - Experiment: {experiment.name}")
    print(f"  - Artifact Location: {experiment.artifact_location}")

    return experiment


if __name__ == "__main__":
    initialize_mlflow()
