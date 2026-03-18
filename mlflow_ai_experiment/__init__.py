"""
Package initialization for src module.
"""

from .data_loader import load_imdb_dataset, save_dataset_splits
from .evaluation import compute_metrics, evaluate_model
from .experiment_tracker import (  # type: ignore
    create_experiment_tracker,
    get_or_create_family_experiment,
    load_config,
    log_model_artifact,
    log_predictions,
    set_standard_tags,
    setup_mlflow_tracking,
)
from . import experiment_tracker
from .models.classical import create_model
from .preprocessing import clean_text, preprocess_dataset

__all__ = [
    "load_imdb_dataset",
    "save_dataset_splits",
    "preprocess_dataset",
    "clean_text",
    "create_model",
    "evaluate_model",
    "compute_metrics",
    "create_experiment_tracker",
    "get_or_create_family_experiment",
    "load_config",
    "log_model_artifact",
    "log_predictions",
    "set_standard_tags",
    "setup_mlflow_tracking",
]
