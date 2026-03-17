"""
Data versioning utilities using checksums.
Provides deterministic versioning of datasets based on content hashes.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import pandas as pd
import yaml


def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate checksum hash of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)

    Returns:
        Hexadecimal string of the file hash
    """
    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def calculate_dataframe_checksum(df: pd.DataFrame, algorithm: str = "sha256") -> str:
    """
    Calculate checksum of a DataFrame by hashing its sorted content.

    Args:
        df: Pandas DataFrame
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal string of the DataFrame hash
    """
    # Sort by index to ensure consistent ordering
    df_sorted = df.sort_index()

    # Convert to bytes (use CSV format with consistent settings)
    data_bytes = df_sorted.to_csv(index=False).encode("utf-8")

    hash_func = hashlib.new(algorithm)
    hash_func.update(data_bytes)

    return hash_func.hexdigest()


def calculate_dataset_version(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    preprocessing_params: Optional[Dict] = None,
    algorithm: str = "sha256",
) -> Dict[str, str]:
    """
    Calculate version identifiers for all dataset splits.

    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
        test_df: Test DataFrame
        preprocessing_params: Dictionary of preprocessing parameters used
        algorithm: Hash algorithm

    Returns:
        Dictionary with checksums for each split and combined version
    """
    versions = {
        "train": calculate_dataframe_checksum(train_df, algorithm),
        "validation": calculate_dataframe_checksum(val_df, algorithm),
        "test": calculate_dataframe_checksum(test_df, algorithm),
    }

    # Create combined version that includes preprocessing params
    combined_data = {
        "splits": versions,
        "preprocessing": preprocessing_params or {},
        "algorithm": algorithm,
    }

    combined_str = json.dumps(combined_data, sort_keys=True)
    versions["dataset"] = hashlib.new(algorithm, combined_str.encode()).hexdigest()

    return versions


def save_version_manifest(
    versions: Dict[str, str],
    output_path: str = "data/version_manifest.yaml",
) -> None:
    """
    Save dataset version information to a manifest file.

    Args:
        versions: Dictionary from calculate_dataset_version()
        output_path: Path to save the manifest file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        yaml.dump(
            {"dataset_versions": versions, "timestamp": pd.Timestamp.now().isoformat()},
            f,
            default_flow_style=False,
        )

    print(f"✓ Dataset version manifest saved to: {output_path}")


def load_version_manifest(
    input_path: str = "data/version_manifest.yaml",
) -> Optional[Dict]:
    """
    Load dataset version manifest from file.

    Args:
        input_path: Path to the manifest file

    Returns:
        Dictionary with version info or None if file doesn't exist
    """
    if not os.path.exists(input_path):
        return None

    with open(input_path, "r") as f:
        manifest = yaml.safe_load(f)

    return manifest


def verify_dataset_integrity(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    manifest_path: str = "data/version_manifest.yaml",
    algorithm: str = "sha256",
) -> bool:
    """
    Verify that current dataset matches stored version.

    Args:
        train_df, val_df, test_df: Current DataFrames
        manifest_path: Path to stored manifest
        algorithm: Hash algorithm to use

    Returns:
        True if integrity check passes, False otherwise
    """
    manifest = load_version_manifest(manifest_path)

    if manifest is None:
        print("⚠ No version manifest found. Cannot verify integrity.")
        return False

    current_versions = calculate_dataset_version(
        train_df, val_df, test_df, algorithm=algorithm
    )
    stored_versions = manifest.get("dataset_versions", {})

    # Compare checksums
    for split in ["train", "validation", "test"]:
        if current_versions[split] != stored_versions.get(split):
            print(f"❌ {split} split has been modified!")
            print(f"   Expected: {stored_versions.get(split)}")
            print(f"   Actual:   {current_versions[split]}")
            return False

    print("✓ Dataset integrity verified - all splits match stored versions")
    return True


def get_dataset_version_string(versions: Dict[str, str]) -> str:
    """
    Generate a compact version string from version dictionary.

    Args:
        versions: Dictionary from calculate_dataset_version()

    Returns:
        Short version string like "v1.0-{hash[:8]}"
    """
    dataset_hash = versions["dataset"][:8]
    return f"v1.0-{dataset_hash}"


def track_dataset_with_mlflow(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    preprocessing_params: Optional[Dict] = None,
    artifact_dir: str = "data_artifacts",
) -> None:
    """
    Log dataset information to the current MLFlow run.

    Args:
        train_df, val_df, test_df: Dataset splits
        preprocessing_params: Preprocessing configuration
        artifact_dir: Directory to save dataset artifacts within MLFlow
    """
    import mlflow

    # Calculate versions
    versions = calculate_dataset_version(
        train_df, val_df, test_df, preprocessing_params
    )

    # Log dataset statistics
    mlflow.log_params(
        {
            "data.train_samples": len(train_df),
            "data.validation_samples": len(val_df),
            "data.test_samples": len(test_df),
            "data.version": get_dataset_version_string(versions),
            "data.dataset_hash": versions["dataset"],
        }
    )

    # Log class distribution
    for split_name, df in [
        ("train", train_df),
        ("validation", val_df),
        ("test", test_df),
    ]:
        class_dist = df["label"].value_counts().sort_index().to_dict()
        for label, count in class_dist.items():
            mlflow.log_metric(f"data.{split_name}.class_{label}_count", count)

    # Save and log dataset files as artifacts
    os.makedirs("temp_data", exist_ok=True)

    train_path = "temp_data/train.csv"
    val_path = "temp_data/validation.csv"
    test_path = "temp_data/test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    mlflow.log_artifact(train_path, artifact_dir)
    mlflow.log_artifact(val_path, artifact_dir)
    mlflow.log_artifact(test_path, artifact_dir)

    # Clean up temp files
    os.remove(train_path)
    os.remove(val_path)
    os.remove(test_path)
    os.rmdir("temp_data")

    print(
        f"✓ Dataset logged to MLFlow with version: {get_dataset_version_string(versions)}"
    )
