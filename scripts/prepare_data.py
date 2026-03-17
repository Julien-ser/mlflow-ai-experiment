#!/usr/bin/env python
"""
Script to prepare the IMDB dataset.
This downloads the dataset, creates CSV splits, and logs to MLFlow.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_loader import load_and_log_dataset

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

    print(f"\nDataset prepared successfully!")
    print(f"Train samples: {len(train_df)}")
    print(f"Validation samples: {len(val_df)}")
    print(f"Test samples: {len(test_df)}")
    print(f"\nFiles saved to data/")
    print(f"Version manifest created at data/version_manifest.yaml")
    print(f"Dataset logged to MLFlow")
