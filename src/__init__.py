"""
Package initialization for src module.
"""

from .train import train_baseline_model
from .data_loader import load_imdb_dataset, save_dataset_splits
from .preprocessing import preprocess_dataset, clean_text
from .models.classical import create_model
from .evaluation import evaluate_model, compute_metrics

__all__ = [
    "train_baseline_model",
    "load_imdb_dataset",
    "save_dataset_splits",
    "preprocess_dataset",
    "clean_text",
    "create_model",
    "evaluate_model",
    "compute_metrics",
]
