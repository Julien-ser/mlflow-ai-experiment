"""
Training pipeline for classical ML models.
"""

import yaml
import os
import mlflow
from mlflow.tracking import MlflowClient
from .data_loader import load_imdb_dataset
from .preprocessing import preprocess_dataset
from .models.classical import create_model
from .evaluation import evaluate_model


def setup_mlflow(config_path="config.yaml"):
    """Set up MLFlow tracking."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    tracking_uri = config["tracking"]["uri"]
    experiment_name = config["experiment"]["name"]

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    return config


def train_baseline_model(model_name, config_path="config.yaml"):
    """
    Train baseline model with MLFlow tracking.

    Args:
        model_name: Name of the model to train (e.g., 'logistic_regression')
        config_path: Path to configuration file

    Returns:
        Tuple of (trained_model, evaluation_results)
    """
    # Load configuration
    config = setup_mlflow(config_path)

    # Load and preprocess data
    print("Loading dataset...")
    train_df, val_df, test_df = load_imdb_dataset(config_path)

    print("Preprocessing data...")
    processed_data = preprocess_dataset(train_df, val_df, test_df)

    X_train, y_train = processed_data["train"]
    X_val, y_val = processed_data["val"]
    X_test, y_test = processed_data["test"]

    # Create model
    print(f"Training {model_name}...")
    model = create_model(model_name)

    # Train with MLFlow tracking
    with mlflow.start_run(run_name=model_name) as run:
        # Log configuration
        mlflow.log_param("model_name", model_name)
        mlflow.log_param("dataset", "imdb")
        mlflow.log_param("preprocessing", "tfidf")

        # Log dataset info
        mlflow.log_param("train_samples", len(train_df))
        mlflow.log_param("val_samples", len(val_df))
        mlflow.log_param("test_samples", len(test_df))
        mlflow.log_param("n_features", X_train.shape[1])

        # Train model
        train_metrics = model.train(X_train, y_train, X_val, y_val)

        # Log training metrics
        mlflow.log_metric("train_accuracy", train_metrics["train_accuracy"])
        mlflow.log_metric("val_accuracy", train_metrics["val_accuracy"])

        # Evaluate on test set
        print("Evaluating on test set...")
        test_results = evaluate_model(model, X_test, y_test, log_to_mlflow=True)

        # Log model
        model.log_to_mlflow(
            experiment_name=config["experiment"]["name"], run_name=model_name
        )

        # Log vectorizer as artifact
        import joblib

        vectorizer_path = "vectorizer.pkl"
        joblib.dump(processed_data["vectorizer"], vectorizer_path)
        mlflow.log_artifact(vectorizer_path)
        os.remove(vectorizer_path)

        print(f"Run ID: {run.info.run_id}")
        print(f"Test Accuracy: {test_results['accuracy']:.4f}")
        print(f"Test F1: {test_results['f1']:.4f}")

        return model, test_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train baseline model")
    parser.add_argument(
        "--model",
        type=str,
        default="logistic_regression",
        choices=["logistic_regression", "svm", "random_forest"],
        help="Model to train",
    )
    parser.add_argument(
        "--config", type=str, default="config.yaml", help="Path to configuration file"
    )

    args = parser.parse_args()

    model, results = train_baseline_model(args.model, args.config)
