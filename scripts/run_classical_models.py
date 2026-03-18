"""
Script to train and evaluate all classical ML models (Logistic Regression, SVM, Random Forest, XGBoost).
This provides a comprehensive comparison baseline against transformer models.
"""

import os
import sys

import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import mlflow
from sklearn.metrics import classification_report

from src.data_loader import load_imdb_dataset  # type: ignore
from src.models.classical import LogisticRegressionModel  # type: ignore
from src.models.classical import RandomForestModel, SVMModel, XGBoostModel
from src.preprocessing import preprocess_dataset  # type: ignore


def train_and_evaluate_model(
    model_wrapper,
    model_name,
    X_train,
    y_train,
    X_val,
    y_val,
    X_test,
    y_test,
    experiment_name="classical_models",
):
    """
    Train and evaluate a single model with MLflow logging.

    Returns:
        Dictionary with model metrics and run_id
    """
    print(f"\n{'=' * 60}")
    print(f"Training {model_name}...")
    print(f"{'=' * 60}")

    # Train the model
    results = model_wrapper.train(X_train, y_train, X_val, y_val)
    print(f"Training accuracy: {results['train_accuracy']:.4f}")
    print(f"Validation accuracy: {results['val_accuracy']:.4f}")

    # Log to MLflow with test evaluation
    run_id = model_wrapper.log_to_mlflow(
        experiment_name=experiment_name,
        run_name=model_name,
        X_test=X_test,
        y_test=y_test,
    )

    # Generate predictions on test set
    y_pred = model_wrapper.predict(X_test)

    # Calculate detailed metrics
    metrics = {
        "model": model_name,
        "run_id": run_id,
        "train_accuracy": results["train_accuracy"],
        "val_accuracy": results["val_accuracy"],
    }

    # Add test metrics
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    metrics["test_accuracy"] = accuracy_score(y_test, y_pred)
    metrics["test_precision"] = precision_score(y_test, y_pred, zero_division="warn")
    metrics["test_recall"] = recall_score(y_test, y_pred, zero_division="warn")
    metrics["test_f1"] = f1_score(y_test, y_pred, zero_division="warn")

    print(f"Test accuracy: {metrics['test_accuracy']:.4f}")
    print(f"Test F1 score: {metrics['test_f1']:.4f}")

    # Print classification report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division="warn"))

    # Save model to models directory
    model_dir = f"../models/classical/{model_name}"
    os.makedirs(model_dir, exist_ok=True)
    model_path = f"{model_dir}/model.pkl"
    model_wrapper.save_model(model_path)
    print(f"Model saved to {model_path}")

    # Log model artifact path as MLflow tag
    with mlflow.start_run(run_id=run_id):
        mlflow.set_tag("model_path", model_path)

    return metrics


def main():
    """Run classical models training and evaluation pipeline."""
    print("=" * 80)
    print("CLASSICAL MODELS TRAINING PIPELINE")
    print("=" * 80)

    # Set MLflow experiment
    mlflow.set_experiment("classical_models_comparison")

    # Load and preprocess data
    print("\n[1/4] Loading IMDB dataset...")
    train_df, val_df, test_df = load_imdb_dataset()

    print("[2/4] Preprocessing data and extracting TF-IDF features...")
    processed_data = preprocess_dataset(train_df, val_df, test_df)

    X_train, y_train = processed_data["train"]
    X_val, y_val = processed_data["val"]
    X_test, y_test = processed_data["test"]

    # Convert to proper format for sklearn (if texts, need to vectorize)
    # The preprocessed data should already be numeric features from TF-IDF
    print(f"Training data shape: {X_train.shape}")
    print(f"Validation data shape: {X_val.shape}")
    print(f"Test data shape: {X_test.shape}")

    # Define models to train
    models_config = [
        (
            "logistic_regression",
            LogisticRegressionModel(
                params={
                    "C": 1.0,
                    "max_iter": 1000,
                    "solver": "liblinear",
                    "random_state": 42,
                }
            ),
        ),
        (
            "svm",
            SVMModel(
                params={
                    "C": 1.0,
                    "max_iter": 2000,
                    "random_state": 42,
                }
            ),
        ),
        (
            "random_forest",
            RandomForestModel(
                params={
                    "n_estimators": 100,
                    "max_depth": 20,
                    "min_samples_split": 5,
                    "random_state": 42,
                    "n_jobs": -1,
                }
            ),
        ),
        (
            "xgboost",
            XGBoostModel(
                params={
                    "n_estimators": 100,
                    "max_depth": 6,
                    "learning_rate": 0.1,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "random_state": 42,
                    "n_jobs": -1,
                    "eval_metric": "logloss",
                }
            ),
        ),
    ]

    # Train and evaluate all models
    print(f"\n[3/4] Training {len(models_config)} models...")
    all_metrics = []

    for model_name, model_wrapper in models_config:
        metrics = train_and_evaluate_model(
            model_wrapper,
            model_name,
            X_train,
            y_train,
            X_val,
            y_val,
            X_test,
            y_test,
            experiment_name="classical_models_comparison",
        )
        all_metrics.append(metrics)

    # Generate comparison table
    print("\n[4/4] Generating comparison summary...")
    print("\n" + "=" * 80)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 80)

    comparison_df = pd.DataFrame(all_metrics)
    comparison_df = comparison_df.set_index("model")
    comparison_df = comparison_df.round(4)

    print("\nTest Metrics:")
    test_metrics_cols = [c for c in comparison_df.columns if c.startswith("test_")]
    print(comparison_df[test_metrics_cols].to_string())

    print("\nAll Metrics:")
    print(comparison_df.to_string())

    # Save comparison to CSV
    csv_path = "../results/classical_models_comparison.csv"
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    comparison_df.to_csv(csv_path)
    print(f"\nComparison saved to {csv_path}")

    # Log comparison to MLflow
    with mlflow.start_run(run_name="comparison_summary") as run:
        for model_name, row in comparison_df.iterrows():
            for col in test_metrics_cols:
                mlflow.log_metric(f"{model_name}_{col}", float(row[col]))
        mlflow.log_artifact(csv_path)
        print(f"\nComparison logged to MLflow run: {run.info.run_id}")

    print("\n" + "=" * 80)
    print("CLASSICAL MODELS TRAINING COMPLETE!")
    print("=" * 80)

    return comparison_df


if __name__ == "__main__":
    results = main()
