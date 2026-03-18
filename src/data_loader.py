"""
Data loader for IMDB dataset using HuggingFace datasets library.
"""

import os
from typing import Dict, Optional

import pandas as pd  # type: ignore
import yaml  # type: ignore
from datasets import load_dataset  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore

from .data_utils import prepare_data_for_mlflow
from .data_versioning import calculate_dataset_version, save_version_manifest


def load_imdb_dataset(config_path="config.yaml"):
    """Load and prepare IMDB dataset with train/validation/test splits."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    data_config = config["data"]

    # Load dataset from HuggingFace
    dataset = load_dataset(data_config["dataset_name"])

    # Get train and test splits
    train_data = dataset[data_config["train_split"]]
    test_data = dataset[data_config["test_split"]]

    # Split training data into train and validation
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        train_data["text"],
        train_data["label"],
        test_size=data_config["validation_split_ratio"],
        random_state=config["training"]["random_seed"],
        stratify=train_data["label"],
    )

    # Create DataFrames
    train_df = pd.DataFrame({"text": train_texts, "label": train_labels})
    val_df = pd.DataFrame({"text": val_texts, "label": val_labels})
    test_df = pd.DataFrame({"text": test_data["text"], "label": test_data["label"]})

    return train_df, val_df, test_df


def save_dataset_splits(train_df, val_df, test_df, output_dir="data"):
    """Save dataset splits to CSV files."""
    os.makedirs(output_dir, exist_ok=True)

    train_df.to_csv(f"{output_dir}/train.csv", index=False)
    val_df.to_csv(f"{output_dir}/validation.csv", index=False)
    test_df.to_csv(f"{output_dir}/test.csv", index=False)

    print(f"Dataset splits saved to {output_dir}/")


def load_and_log_dataset(
    config_path="config.yaml",
    log_to_mlflow: bool = True,
    preprocessing_params: Optional[Dict] = None,
) -> tuple:
    """
    Load dataset and optionally log to MLFlow with versioning.

    Args:
        config_path: Path to config file
        log_to_mlflow: Whether to log dataset info to MLFlow
        preprocessing_params: Preprocessing parameters to include in versioning

    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    train_df, val_df, test_df = load_imdb_dataset(config_path)

    if log_to_mlflow:
        prepare_data_for_mlflow(
            train_df,
            val_df,
            test_df,
            preprocessing_params=preprocessing_params,
            include_artifacts=True,
        )

    # Save to disk
    save_dataset_splits(train_df, val_df, test_df)

    # Calculate and save version manifest
    versions = calculate_dataset_version(
        train_df, val_df, test_df, preprocessing_params
    )
    save_version_manifest(versions)

    return train_df, val_df, test_df


if __name__ == "__main__":
    train_df, val_df, test_df = load_imdb_dataset()
    save_dataset_splits(train_df, val_df, test_df)

    print(f"Train set: {len(train_df)} samples")
    print(f"Validation set: {len(val_df)} samples")
    print(f"Test set: {len(test_df)} samples")
