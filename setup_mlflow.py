#!/usr/bin/env python3
"""
MLFlow Tracking Setup Script
Initializes MLflow tracking infrastructure for the experiment tracking project.
"""

import os
import yaml
import mlflow
from pathlib import Path


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


def get_or_create_experiment(config: dict) -> mlflow.entities.Experiment:
    """Get existing experiment or create new one."""

    experiment_name = config["experiment"]["name"]
    artifact_location = config["experiment"].get("artifact_location", "mlruns")

    # Try to get existing experiment
    experiment = mlflow.get_experiment_by_name(experiment_name)

    if experiment is None:
        # Create new experiment
        experiment_id = mlflow.create_experiment(
            name=experiment_name,
            artifact_location=artifact_location,
            tags=config["experiment"].get("tags", {}),
        )
        experiment = mlflow.get_experiment(experiment_id)
        print(f"✓ Created new experiment: {experiment_name} (ID: {experiment_id})")
    else:
        print(
            f"✓ Using existing experiment: {experiment_name} (ID: {experiment.experiment_id})"
        )

    return experiment


def initialize_mlflow() -> mlflow.entities.Experiment:
    """
    Initialize MLflow tracking and return the experiment object.

    Returns:
        MLflow Experiment object
    """
    config = load_config()
    setup_mlflow_tracking(config)
    experiment = get_or_create_experiment(config)

    print(f"\n✓ MLflow initialization complete!")
    print(f"  - Tracking URI: {mlflow.get_tracking_uri()}")
    print(f"  - Experiment: {experiment.name}")
    print(f"  - Artifact Location: {experiment.artifact_location}")

    return experiment


if __name__ == "__main__":
    initialize_mlflow()
