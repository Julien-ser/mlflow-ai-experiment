#!/usr/bin/env python
"""
Command-line script to evaluate a trained model.

Usage:
    python -m mlflow_ai_experiment.evaluate --model-path <path> --data-path <path>
    or
    python src/evaluate.py --model-path <path> --data-path <path>

This script loads a model and test data, computes evaluation metrics (accuracy,
precision, recall, F1, confusion matrix, inference latency, memory footprint),
and optionally logs them to MLflow.
"""

import argparse
import sys
from .evaluation import evaluate_model
import joblib
import pandas as pd
import mlflow


def main(args=None):
    parser = argparse.ArgumentParser(description="Evaluate a trained model.")
    parser.add_argument(
        "--model-path",
        required=True,
        help="Path to the saved model (joblib format)",
    )
    parser.add_argument(
        "--data-path",
        required=True,
        help="Path to test data (CSV with features and label; last column assumed to be label)",
    )
    parser.add_argument(
        "--log-mlflow",
        action="store_true",
        help="Log metrics and parameters to MLflow",
    )
    parsed_args = parser.parse_args(args)

    # Load model
    try:
        model = joblib.load(parsed_args.model_path)
    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        sys.exit(1)

    # Load data
    try:
        df = pd.read_csv(parsed_args.data_path)
        # Assume last column is the label
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values
    except Exception as e:
        print(f"Error loading data: {e}", file=sys.stderr)
        sys.exit(1)

    # Run evaluation with optional MLflow logging
    if parsed_args.log_mlflow:
        with mlflow.start_run():
            results = evaluate_model(model, X, y, log_to_mlflow=True)
    else:
        results = evaluate_model(model, X, y, log_to_mlflow=False)

    # Print results
    print("Evaluation results:")
    for key, value in results.items():
        if key == "confusion_matrix":
            print(f"{key}:")
            for row in value:
                print(f"  {row}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
