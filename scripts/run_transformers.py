"""
Script to train and evaluate all transformer models (BERT, RoBERTa, DeBERTa, XLNet, ELECTRA, ALBERT, DistilBERT, GPT2).
This provides comprehensive comparison of state-of-the-art language models.
"""

import os
import sys

import pandas as pd
import yaml

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import time

import mlflow
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from src.data_loader import load_imdb_dataset  # type: ignore
from src.models.transformers import create_transformer_model  # type: ignore


def load_model_zoo_config(config_path="config/models.yaml"):
    """Load model zoo configurations."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config["model_zoo"]


def tokenize_dataset(model_wrapper, texts, labels=None):
    """Tokenize dataset for transformer model."""
    return model_wrapper.tokenize_data(texts, labels=labels)


def train_and_evaluate_transformer(
    model_type,
    config_name,
    model_config,
    train_texts,
    train_labels,
    val_texts,
    val_labels,
    test_texts,
    test_labels,
    experiment_name="transformers_comparison",
):
    """
    Train and evaluate a single transformer model with MLflow logging.

    Args:
        model_type: Type of transformer (e.g., 'bert', 'roberta')
        config_name: Name of the configuration variant (e.g., 'base', 'large')
        model_config: Dictionary with model hyperparameters
        train/val/test texts and labels: Data splits
        experiment_name: MLflow experiment name

    Returns:
        Dictionary with model metrics and run_id
    """
    print(f"\n{'=' * 60}")
    print(f"Training {model_type.upper()} ({config_name})...")
    print(f"Model: {model_config['model_name']}")
    print(f"{'=' * 60}")

    # Create model
    model = create_transformer_model(model_type, **model_config)

    # Load tokenizer
    print("Loading tokenizer...")
    model.load_tokenizer()

    # Tokenize data
    print("Tokenizing datasets...")
    train_dataset = tokenize_dataset(model, train_texts, train_labels)
    val_dataset = tokenize_dataset(model, val_texts, val_labels)

    # Train model
    print("Training model...")
    train_start = time.time()
    model.train(train_dataset, val_dataset, experiment_name=experiment_name)
    train_time = time.time() - train_start

    # Evaluate on test set
    print("Evaluating on test set...")
    test_preds = model.predict(test_texts)

    # Calculate metrics
    test_accuracy = accuracy_score(test_labels, test_preds)
    test_precision = precision_score(test_labels, test_preds, zero_division="warn")
    test_recall = recall_score(test_labels, test_preds, zero_division="warn")
    test_f1 = f1_score(test_labels, test_preds, zero_division="warn")

    # Measure inference latency
    latency_start = time.time()
    _ = model.predict(test_texts[:100])
    inference_latency = (time.time() - latency_start) / len(test_texts[:100])

    active_run = mlflow.active_run()
    metrics = {
        "model": f"{model_type}_{config_name}",
        "model_name": model_config["model_name"],
        "run_id": active_run.info.run_id if active_run else None,
        "train_accuracy": None,  # Not directly available from trainer
        "val_accuracy": None,
        "test_accuracy": test_accuracy,
        "test_precision": test_precision,
        "test_recall": test_recall,
        "test_f1": test_f1,
        "train_time_seconds": train_time,
        "inference_latency_ms": inference_latency * 1000,
        "batch_size": model_config.get("batch_size", 16),
        "learning_rate": model_config.get("learning_rate", 2e-5),
    }

    print(f"Test accuracy: {test_accuracy:.4f}")
    print(f"Test F1 score: {test_f1:.4f}")
    print(f"Inference latency: {inference_latency * 1000:.2f} ms per sample")
    print(f"Training time: {train_time:.2f} seconds")

    # Print classification report
    from sklearn.metrics import classification_report

    print("\nClassification Report:")
    print(classification_report(test_labels, test_preds, zero_division="warn"))

    # Save predictions as artifact
    predictions_dir = "../results/predictions"
    os.makedirs(predictions_dir, exist_ok=True)
    predictions_path = f"{predictions_dir}/{model_type}_{config_name}_predictions.csv"
    predictions_df = pd.DataFrame(
        {
            "text": test_texts,
            "true_label": test_labels,
            "predicted_label": test_preds,
        }
    )
    predictions_df.to_csv(predictions_path, index=False)
    print(f"Predictions saved to {predictions_path}")

    # Save model to models directory
    model_dir = f"../models/transformers/{model_type}_{config_name}"
    os.makedirs(model_dir, exist_ok=True)
    model_path = f"{model_dir}/model"
    model.save_model(model_path)
    print(f"Model saved to {model_path}")

    # Log test metrics and artifacts in a dedicated MLflow run (training was logged by model.train)
    with mlflow.start_run(run_name=f"{model_type}_{config_name}") as run:
        # Log test metrics
        mlflow.log_metric("test_accuracy", float(test_accuracy))
        mlflow.log_metric("test_precision", float(test_precision))
        mlflow.log_metric("test_recall", float(test_recall))
        mlflow.log_metric("test_f1", float(test_f1))
        mlflow.log_metric("train_time_seconds", float(train_time))
        mlflow.log_metric("inference_latency_ms", float(inference_latency * 1000))

        # Log hyperparameters
        for key in [
            "dropout",
            "learning_rate",
            "batch_size",
            "max_seq_length",
            "num_train_epochs",
            "weight_decay",
            "warmup_steps",
        ]:
            if key in model_config:
                mlflow.log_param(key, model_config[key])

        # Log tags
        mlflow.set_tag("model_type", model_type)
        mlflow.set_tag("config_name", config_name)
        mlflow.set_tag("model_path", model_path)
        mlflow.set_tag("framework", "transformers")
        mlflow.set_tag("dataset_version", "v1.0")
        mlflow.set_tag("preprocessing_config", "standard")

        # Log predictions artifact
        mlflow.log_artifact(predictions_path, "predictions")

        metrics["run_id"] = run.info.run_id

    return metrics, model


def main():
    """Run transformer models training and evaluation pipeline."""
    print("=" * 80)
    print("TRANSFORMER MODELS TRAINING PIPELINE")
    print("=" * 80)

    # Set MLflow experiment
    mlflow.set_experiment("transformers_comparison")

    # Load model zoo config
    print("\n[1/5] Loading model zoo configuration...")
    model_zoo = load_model_zoo_config()
    print(f"Available model families: {list(model_zoo.keys())}")

    # Load and preprocess data
    print("\n[2/5] Loading IMDB dataset...")
    train_df, val_df, test_df = load_imdb_dataset()

    train_texts = train_df["text"].tolist()
    train_labels = train_df["label"].tolist()
    val_texts = val_df["text"].tolist()
    val_labels = val_df["label"].tolist()
    test_texts = test_df["text"].tolist()
    test_labels = test_df["label"].tolist()

    print(f"Training samples: {len(train_texts)}")
    print(f"Validation samples: {len(val_texts)}")
    print(f"Test samples: {len(test_texts)}")

    # Define models to train (all variants from model zoo)
    models_to_train = []
    for model_type, variants in model_zoo.items():
        for variant_name, config in variants.items():
            models_to_train.append((model_type, variant_name, config))

    print(f"\n[3/5] Training {len(models_to_train)} transformer models...")

    # Train and evaluate all models
    all_metrics = []
    trained_models = []

    for model_type, variant_name, model_config in models_to_train:
        try:
            metrics, trained_model = train_and_evaluate_transformer(
                model_type,
                variant_name,
                model_config,
                train_texts,
                train_labels,
                val_texts,
                val_labels,
                test_texts,
                test_labels,
                experiment_name="transformers_comparison",
            )
            all_metrics.append(metrics)
            trained_models.append((model_type, variant_name, trained_model))
        except Exception as e:
            print(f"ERROR training {model_type} ({variant_name}): {e}")
            continue

    # Generate comparison table
    print("\n[4/5] Generating comparison summary...")
    print("\n" + "=" * 80)
    print("TRANSFORMER MODELS COMPARISON SUMMARY")
    print("=" * 80)

    comparison_df = None
    if all_metrics:
        comparison_df = pd.DataFrame(all_metrics)
        comparison_df = comparison_df.set_index("model")
        comparison_df = comparison_df.round(4)

        print("\nTest Metrics:")
        test_metrics_cols = [
            "test_accuracy",
            "test_precision",
            "test_recall",
            "test_f1",
            "inference_latency_ms",
            "train_time_seconds",
        ]
        print(comparison_df[test_metrics_cols].to_string())

        print("\nAll Metrics:")
        print(comparison_df.to_string())

        # Save comparison to CSV
        csv_path = "../results/transformers_comparison.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        comparison_df.to_csv(csv_path)
        print(f"\nComparison saved to {csv_path}")

        # Log comparison to MLflow
        with mlflow.start_run(run_name="comparison_summary") as run:
            for model_name, row in comparison_df.iterrows():  # type: ignore
                for col in test_metrics_cols:  # type: ignore
                    value = float(row[col])
                    mlflow.log_metric(f"{model_name}_{col}", value)  # type: ignore
            mlflow.log_artifact(csv_path)
            print(f"\nComparison logged to MLflow run: {run.info.run_id}")
    else:
        print("No models completed training successfully.")

    print("\n" + "=" * 80)
    print("TRANSFORMER MODELS TRAINING COMPLETE!")
    print("=" * 80)

    return comparison_df


if __name__ == "__main__":
    results = main()
