#!/usr/bin/env python
"""
Run hyperparameter optimization via command line.

This script provides a CLI for the hyperparameter optimization framework,
supporting both Optuna and Ray Tune backends.
"""

import argparse
import os
import sys

import mlflow
import numpy as np

from mlflow_ai_experiment import hyperopt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hyperparameter optimization for ML models."
    )
    parser.add_argument(
        "--model-type",
        required=True,
        choices=[
            "bert",
            "roberta",
            "deberta",
            "distilbert",
            "albert",
            "logistic_regression",
            "svm",
            "random_forest",
            "xgboost",
        ],
        help="Model type to optimize.",
    )
    parser.add_argument(
        "--backend",
        default="optuna",
        choices=["optuna", "ray"],
        help="Optimization backend (default: optuna).",
    )
    parser.add_argument(
        "--n-trials", type=int, default=20, help="Number of trials (default: 20)."
    )
    parser.add_argument(
        "--experiment-name",
        default="hyperopt_experiment",
        help="MLflow experiment name (default: hyperopt_experiment).",
    )
    parser.add_argument(
        "--mlflow-uri",
        default=os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"),
        help="MLflow tracking URI (default from env or sqlite:///mlflow.db).",
    )
    parser.add_argument(
        "--X-train",
        help="Path to X_train.npy for classical models.",
    )
    parser.add_argument(
        "--y-train",
        help="Path to y_train.npy for classical models.",
    )
    parser.add_argument(
        "--X-val",
        help="Path to X_val.npy for classical models.",
    )
    parser.add_argument(
        "--y-val",
        help="Path to y_val.npy for classical models.",
    )
    parser.add_argument(
        "--train-dataset",
        help="Path to tokenized train dataset for transformer models.",
    )
    parser.add_argument(
        "--val-dataset",
        help="Path to tokenized val dataset for transformer models.",
    )
    parser.add_argument(
        "--dataset-version",
        default="v1.0",
        help="Dataset version string for tagging.",
    )
    parser.add_argument(
        "--preprocessing-config",
        default="standard",
        help="Preprocessing configuration name.",
    )

    args = parser.parse_args()

    mlflow.set_tracking_uri(args.mlflow_uri)

    # Determine model category
    transformer_models = {"bert", "roberta", "deberta", "distilbert", "albert"}
    is_transformer = args.model_type in transformer_models

    if is_transformer:
        if not args.train_dataset or not args.val_dataset:
            raise ValueError(
                "Transformer models require --train-dataset and --val-dataset arguments."
            )
        # For demonstration, we expect a torch-saved dataset.
        try:
            import torch

            train_dataset = torch.load(args.train_dataset)
            val_dataset = torch.load(args.val_dataset)
        except Exception as e:
            print(
                f"Error loading transformer datasets: {e}. "
                "Make sure to provide torch-saved datasets.",
                file=sys.stderr,
            )
            sys.exit(1)
        X_train = y_train = X_val = y_val = None
    else:
        if not all([args.X_train, args.y_train, args.X_val, args.y_val]):
            raise ValueError(
                "Classical models require --X-train, --y-train, --X-val, --y-val arguments."
            )
        X_train = np.load(args.X_train)
        y_train = np.load(args.y_train)
        X_val = np.load(args.X_val)
        y_val = np.load(args.y_val)
        train_dataset = val_dataset = None

    study = hyperopt.optimize_model(
        model_type=args.model_type,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        experiment_name=args.experiment_name,
        backend=args.backend,
        n_trials=args.n_trials,
        dataset_version=args.dataset_version,
        preprocessing_config=args.preprocessing_config,
    )

    print("Optimization completed.")
    print(f"Best value: {study.best_value}")
    print(f"Best parameters: {study.best_params}")


if __name__ == "__main__":
    main()
