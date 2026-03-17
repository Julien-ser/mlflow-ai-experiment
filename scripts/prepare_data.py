#!/usr/bin/env python
"""
Script to prepare the IMDB dataset.
This downloads the dataset and creates CSV splits.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_loader import load_imdb_dataset, save_dataset_splits

if __name__ == "__main__":
    print("Preparing IMDB dataset...")
    train_df, val_df, test_df = load_imdb_dataset()
    save_dataset_splits(train_df, val_df, test_df)

    print(f"\nDataset prepared successfully!")
    print(f"Train samples: {len(train_df)}")
    print(f"Validation samples: {len(val_df)}")
    print(f"Test samples: {len(test_df)}")
    print(f"\nFiles saved to data/")
