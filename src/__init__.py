"""
Package initialization for src module.
"""

from .data_loader import load_imdb_dataset, save_dataset_splits
from .evaluation import compute_metrics, evaluate_model
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
]
