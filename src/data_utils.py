"""
Data utilities for MLFlow logging.
Provides functions to log dataset statistics, splits, and preprocessing parameters.
"""

import os
import mlflow
import pandas as pd  # type: ignore
from typing import Dict, Any, Optional, List, Tuple
from .data_versioning import (
    calculate_dataset_version,
    get_dataset_version_string,
    track_dataset_with_mlflow,
)


def log_dataset_statistics(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    prefix: str = "data",
) -> None:
    """
    Log basic dataset statistics to MLFlow.

    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
        test_df: Test DataFrame
        prefix: Prefix for metric names
    """
    # Sample counts
    mlflow.log_metrics(
        {
            f"{prefix}.train_samples": len(train_df),
            f"{prefix}.validation_samples": len(val_df),
            f"{prefix}.test_samples": len(test_df),
            f"{prefix}.total_samples": len(train_df) + len(val_df) + len(test_df),
        }
    )

    # Text length statistics
    for split_name, df in [
        ("train", train_df),
        ("validation", val_df),
        ("test", test_df),
    ]:
        text_lengths = df["text"].str.len()
        mlflow.log_metrics(
            {
                f"{prefix}.{split_name}.avg_text_length": text_lengths.mean(),
                f"{prefix}.{split_name}.min_text_length": text_lengths.min(),
                f"{prefix}.{split_name}.max_text_length": text_lengths.max(),
                f"{prefix}.{split_name}.std_text_length": text_lengths.std(),
            }
        )

        # Class distribution
        class_counts = df["label"].value_counts().sort_index()
        for label, count in class_counts.items():
            mlflow.log_metric(f"{prefix}.{split_name}.class_{label}_count", int(count))
            mlflow.log_metric(
                f"{prefix}.{split_name}.class_{label}_percentage",
                float(count / len(df) * 100),
            )


def log_preprocessing_parameters(
    params: Dict[str, Any], prefix: str = "preprocessing"
) -> None:
    """
    Log preprocessing parameters to MLFlow.

    Args:
        params: Dictionary of preprocessing parameters
        prefix: Prefix for parameter names
    """
    # Flatten nested dicts if necessary
    flattened = _flatten_dict(params, prefix)

    # Log parameters
    mlflow.log_params(flattened)


def _flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator between keys

    Returns:
        Flattened dictionary
    """
    items: List[Tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, (list, tuple)):
            # Convert lists to strings for MLFlow
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def log_data_artifacts(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    artifact_dir: str = "data_artifacts",
    save_csv: bool = True,
) -> None:
    """
    Save and log dataset splits as artifacts to MLFlow.

    Args:
        train_df, val_df, test_df: Dataset splits
        artifact_dir: Directory name within MLFlow artifacts
        save_csv: Whether to save as CSV (otherwise use parquet)
    """
    os.makedirs("temp_data_artifacts", exist_ok=True)

    if save_csv:
        train_path = "temp_data_artifacts/train.csv"
        val_path = "temp_data_artifacts/validation.csv"
        test_path = "temp_data_artifacts/test.csv"

        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)
    else:
        train_path = "temp_data_artifacts/train.parquet"
        val_path = "temp_data_artifacts/validation.parquet"
        test_path = "temp_data_artifacts/test.parquet"

        train_df.to_parquet(train_path, index=False)
        val_df.to_parquet(val_path, index=False)
        test_df.to_parquet(test_path, index=False)

    # Log artifacts
    mlflow.log_artifact(train_path, artifact_dir)
    mlflow.log_artifact(val_path, artifact_dir)
    mlflow.log_artifact(test_path, artifact_dir)

    # Clean up
    os.remove(train_path)
    os.remove(val_path)
    os.remove(test_path)
    os.rmdir("temp_data_artifacts")

    print(f"✓ Dataset artifacts logged to: {artifact_dir}/")


def log_data_pipeline_metrics(
    metrics: Dict[str, float],
    prefix: str = "data_pipeline",
) -> None:
    """
    Log data pipeline performance metrics to MLFlow.

    Args:
        metrics: Dictionary of metric names and values
        prefix: Prefix for metric names
    """
    prefixed_metrics = {f"{prefix}.{k}": v for k, v in metrics.items()}
    mlflow.log_metrics(prefixed_metrics)


def create_and_log_data_report(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    report_path: str = "data/data_report.md",
) -> str:
    """
    Create a markdown data report and log it as an artifact.

    Args:
        train_df, val_df, test_df: Dataset splits
        report_path: Where to save the report

    Returns:
        Path to the created report
    """
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w") as f:
        f.write("# Dataset Report\n\n")

        f.write("## Overview\n\n")
        f.write(f"- Train samples: {len(train_df)}\n")
        f.write(f"- Validation samples: {len(val_df)}\n")
        f.write(f"- Test samples: {len(test_df)}\n")
        f.write(f"- Total samples: {len(train_df) + len(val_df) + len(test_df)}\n\n")

        f.write("## Class Distribution\n\n")
        f.write("### Train\n")
        f.write(train_df["label"].value_counts().to_markdown() + "\n\n")  # type: ignore

        f.write("### Validation\n")
        f.write(val_df["label"].value_counts().to_markdown() + "\n\n")  # type: ignore

        f.write("### Test\n")
        f.write(test_df["label"].value_counts().to_markdown() + "\n\n")  # type: ignore

        f.write("## Text Length Statistics\n\n")
        for split_name, df in [
            ("Train", train_df),
            ("Validation", val_df),
            ("Test", test_df),
        ]:
            lengths = df["text"].str.len()
            f.write(f"### {split_name}\n")
            f.write(f"- Mean: {lengths.mean():.1f}\n")
            f.write(f"- Std: {lengths.std():.1f}\n")
            f.write(f"- Min: {lengths.min()}\n")
            f.write(f"- Max: {lengths.max():,}\n\n")

    # Log as artifact if MLFlow is active
    try:
        import mlflow

        if mlflow.active_run():
            mlflow.log_artifact(report_path, "data_reports")
            print(f"✓ Data report logged to MLFlow: {report_path}")
    except ImportError:
        pass

    return report_path


def prepare_data_for_mlflow(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    preprocessing_params: Optional[Dict[str, Any]] = None,
    include_artifacts: bool = True,
) -> None:
    """
    Comprehensive function to log all data-related information to MLFlow.

    Args:
        train_df, val_df, test_df: Dataset splits
        preprocessing_params: Dictionary of preprocessing configuration
        include_artifacts: Whether to log dataset files as artifacts
    """
    import mlflow

    print("Logging dataset information to MLFlow...")

    # Log basic statistics
    log_dataset_statistics(train_df, val_df, test_df)

    # Log preprocessing parameters if provided
    if preprocessing_params:
        log_preprocessing_parameters(preprocessing_params)

    # Version dataset
    versions = calculate_dataset_version(
        train_df, val_df, test_df, preprocessing_params
    )
    mlflow.log_param("data.version", get_dataset_version_string(versions))
    mlflow.log_param("data.dataset_hash", versions["dataset"])

    # Log artifacts if requested
    if include_artifacts:
        log_data_artifacts(train_df, val_df, test_df)

    # Create and log data report
    report_path = create_and_log_data_report(train_df, val_df, test_df)

    print(
        f"✓ Complete data logging finished (version: {get_dataset_version_string(versions)})"
    )
    print(f"  Report: {report_path}")
