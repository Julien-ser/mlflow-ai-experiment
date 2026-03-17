"""
Script to train and evaluate the baseline TF-IDF + Logistic Regression model.
"""

import sys
import os

# Add project root to path for absolute imports
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data_loader import load_imdb_dataset
from src.preprocessing import preprocess_dataset
from src.baseline import BaselineModel
import mlflow


def main():
    """Run baseline training pipeline."""
    print("Loading IMDB dataset...")
    train_df, val_df, test_df = load_imdb_dataset()

    print("Preprocessing data...")
    processed_data = preprocess_dataset(train_df, val_df, test_df)

    X_train, y_train = processed_data["train"]
    X_val, y_val = processed_data["val"]
    X_test, y_test = processed_data["test"]

    print(f"Training data shape: {X_train.shape}")
    print(f"Validation data shape: {X_val.shape}")
    print(f"Test data shape: {X_test.shape}")

    # Create and train baseline model
    baseline = BaselineModel(max_features=5000, ngram_range=(1, 2))

    print("\nTraining baseline model with MLFlow tracking...")
    metrics = baseline.log_to_mlflow(
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        experiment_name="baseline_tfidf_logreg",
        run_name="tfidf_5000_ngram12",
    )

    print("\nBaseline model training complete!")
    print(f"Test Accuracy: {metrics['accuracy']:.4f}")
    print(f"Test F1 Score: {metrics['f1']:.4f}")
    print(f"Test Precision: {metrics['precision']:.4f}")
    print(f"Test Recall: {metrics['recall']:.4f}")

    # Also save model to models directory
    os.makedirs("../models/baseline", exist_ok=True)
    baseline.save("../models/baseline/baseline_model.pkl")
    print("Model saved to ../models/baseline/baseline_model.pkl")


if __name__ == "__main__":
    main()
