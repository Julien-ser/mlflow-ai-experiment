#!/usr/bin/env python
"""
Script to prepare the IMDB dataset.
This downloads the dataset, creates CSV splits, and logs to MLFlow.
"""

import sys
import os

# Add project root to path for absolute imports
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data_loader import load_and_log_dataset  # noqa: E402

if __name__ == "__main__":
    print("Preparing IMDB dataset with MLFlow logging...")

    # Load and log dataset with versioning
    train_df, val_df, test_df = load_and_log_dataset(
        log_to_mlflow=True,
        preprocessing_params={
            "cleaning": "lowercase, remove_html, strip_whitespace",
            "tokenization": "not_applied_yet",
        },
    )

    print("\nDataset prepared successfully!")
    print(f"Train samples: {len(train_df)}")
    print(f"Validation samples: {len(val_df)}")
    print(f"Test samples: {len(test_df)}")
    print("\nFiles saved to data/")
    print("Version manifest created at data/version_manifest.yaml")
    print("Dataset logged to MLFlow")
