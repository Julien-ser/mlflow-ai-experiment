"""
Script to run hyperparameter optimization using Optuna with MLflow integration.
Automatically searches optimal hyperparameters for classical and transformer models.
"""

import argparse
import os
import pickle
import sys

import pandas as pd
import yaml  # type: ignore

# Add project root to path to enable package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mlflow
from mlflow_ai_experiment.data_loader import load_imdb_dataset  # type: ignore
from mlflow_ai_experiment.experiment_tracker import (
    load_config,
    get_or_create_family_experiment,
)
from mlflow_ai_experiment.preprocessing import preprocess_dataset

config = load_config()
DATASET_VERSION = config["tags"]["dataset_version"]
PREPROCESSING_CONFIG = config["tags"]["preprocessing_config"]


def load_hyperparam_config(config_path="config/hyperparams/"):
    """Load hyperparameter search space configurations."""
    classical_path = os.path.join(config_path, "classical.yaml")
    transformers_path = os.path.join(config_path, "transformers.yaml")

    with open(classical_path, "r") as f:
        classical_config = yaml.safe_load(f)

    with open(transformers_path, "r") as f:
        transformers_config = yaml.safe_load(f)

    return classical_config, transformers_config


def preprocess_for_classical(train_df, val_df, test_df):
    """Preprocess data for classical models (TF-IDF features)."""
    print("Preprocessing data for classical models (TF-IDF)...")
    processed_data = preprocess_dataset(train_df, val_df, test_df)

    X_train, y_train = processed_data["train"]
    X_val, y_val = processed_data["val"]
    X_test, y_test = processed_data["test"]

    return X_train, y_train, X_val, y_val, X_test, y_test


def preprocess_for_transformers(train_df, val_df, test_df):
    """Prepare raw text and labels for transformer models."""
    print("Preparing raw text data for transformers...")

    train_texts = train_df["text"].tolist()
    train_labels = train_df["label"].tolist()
    val_texts = val_df["text"].tolist()
    val_labels = val_df["label"].tolist()
    test_texts = test_df["text"].tolist()
    test_labels = test_df["label"].tolist()

    return train_texts, train_labels, val_texts, val_labels, test_texts, test_labels


def save_study_results(study, model_type, output_dir="../results/hyperopt"):
    """Save Optuna study results to disk."""
    os.makedirs(output_dir, exist_ok=True)

    # Save study object
    study_path = os.path.join(output_dir, f"{model_type}_study.pkl")
    with open(study_path, "wb") as f:
        pickle.dump(study, f)

    # Save best parameters as YAML
    params_path = os.path.join(output_dir, f"{model_type}_best_params.yaml")
    with open(params_path, "w") as f:
        yaml.dump(
            {"best_params": study.best_params, "best_value": float(study.best_value)},
            f,
            default_flow_style=False,
        )

    # Save trial history as CSV
    trials_df = pd.DataFrame(
        [
            {
                "trial_number": t.number,
                "value": t.value,
                **t.params,
                "state": str(t.state),
            }
            for t in study.trials
        ]
    )
    csv_path = os.path.join(output_dir, f"{model_type}_trials.csv")
    trials_df.to_csv(csv_path, index=False)

    print(f"Study results saved to {output_dir}/")
    return study_path, params_path, csv_path


def run_hyperopt_classical(
    model_types,
    X_train,
    y_train,
    X_val,
    y_val,
    experiment_name,
    n_trials=20,
    timeout=None,
    dataset_version=DATASET_VERSION,
    preprocessing_config=PREPROCESSING_CONFIG,
):
    """Run hyperparameter optimization for classical models."""
    from mlflow_ai_experiment.hyperopt import optimize_all_classical

    print(f"\n{'=' * 80}")
    print("CLASSICAL HYPERPARAMETER OPTIMIZATION")
    print(f"Models: {model_types}")
    print(f"Trials per model: {n_trials}")
    print(f"{'=' * 80}")

    results = optimize_all_classical(
        model_types=model_types,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        experiment_name=experiment_name,
        n_trials=n_trials,
        dataset_version=dataset_version,
        preprocessing_config=preprocessing_config,
    )

    # Save results for each model
    output_dir = "../results/hyperopt"
    for model_type, study in results.items():
        print(f"\nBest {model_type} - Validation Accuracy: {study.best_value:.4f}")
        print(f"Best parameters: {study.best_params}")
        save_study_results(study, f"classical_{model_type}", output_dir)

    return results


def run_hyperopt_transformers(
    model_types,
    train_texts,
    train_labels,
    val_texts,
    val_labels,
    experiment_name,
    n_trials=20,
    timeout=None,
    dataset_version=DATASET_VERSION,
    preprocessing_config=PREPROCESSING_CONFIG,
):
    """Run hyperparameter optimization for transformer models."""
    from mlflow_ai_experiment.hyperopt import optimize_transformer_model
    from transformers import AutoTokenizer
    import torch

    # Mapping of model_type to pretrained model name
    MODEL_NAMES = {
        "bert": "bert-base-uncased",
        "roberta": "roberta-base",
        "deberta": "microsoft/deberta-v3-base",
        "xlnet": "xlnet-base-cased",
        "electra": "google/electra-base-discriminator",
        "albert": "albert-base-v2",
        "distilbert": "distilbert-base-uncased",
        "gpt2": "gpt2",
    }

    print(f"\n{'=' * 80}")
    print("TRANSFORMER HYPERPARAMETER OPTIMIZATION")
    print(f"Models: {model_types}")
    print(f"Trials per model: {n_trials}")
    print(f"{'=' * 80}")

    results = {}
    for model_type in model_types:
        print(f"\nOptimizing {model_type}...")
        if model_type not in MODEL_NAMES:
            raise ValueError(f"Unknown model type: {model_type}")
        model_name = MODEL_NAMES[model_type]
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Tokenize data
        train_encoding = tokenizer(
            train_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        train_encoding["labels"] = torch.tensor(train_labels)
        val_encoding = tokenizer(
            val_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        val_encoding["labels"] = torch.tensor(val_labels)
        # Run optimization
        study = optimize_transformer_model(
            model_type=model_type,
            train_dataset=train_encoding,
            val_dataset=val_encoding,
            experiment_name=experiment_name,
            n_trials=n_trials,
            timeout=timeout,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
        )
        results[model_type] = study
        print(f"Best accuracy for {model_type}: {study.best_value:.4f}")

    return results


def main():
    """Main hyperparameter optimization pipeline."""
    parser = argparse.ArgumentParser(
        description="Run hyperparameter optimization with Optuna and MLflow"
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        choices=[
            "logistic_regression",
            "svm",
            "random_forest",
            "xgboost",
            "bert",
            "roberta",
            "deberta",
            "xlnet",
            "electra",
            "albert",
            "distilbert",
            "gpt2",
        ],
        help="Model types to optimize",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["classical", "transformer", "both"],
        default="both",
        help="Optimization mode: classical, transformer, or both",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=20,
        help="Number of optimization trials per model",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Timeout in seconds for optimization per model",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="hyperparameter_optimization",
        help="MLflow experiment name",
    )
    parser.add_argument(
        "--dataset-version",
        type=str,
        default=DATASET_VERSION,
        help="Dataset version tag",
    )
    parser.add_argument(
        "--preprocessing-config",
        type=str,
        default=PREPROCESSING_CONFIG,
        help="Preprocessing configuration tag",
    )

    args = parser.parse_args()

    # Determine which models to optimize
    if args.models:
        model_list = args.models
        # Infer mode from model types
        classical_models = [
            m
            for m in model_list
            if m in ["logistic_regression", "svm", "random_forest", "xgboost"]
        ]
        transformer_models = [
            m
            for m in model_list
            if m
            in [
                "bert",
                "roberta",
                "deberta",
                "xlnet",
                "electra",
                "albert",
                "distilbert",
                "gpt2",
            ]
        ]
    else:
        # Default to all models
        classical_models = ["logistic_regression", "svm", "random_forest", "xgboost"]
        transformer_models = ["bert", "roberta", "deberta"]
        # Add more if needed

    print("=" * 80)
    print("HYPERPARAMETER OPTIMIZATION PIPELINE")
    print("=" * 80)
    print(f"Mode: {args.mode}")
    print(
        f"Classical models: {classical_models if args.mode in ['classical', 'both'] else []}"
    )
    print(
        f"Transformer models: {transformer_models if args.mode in ['transformer', 'both'] else []}"
    )
    print(f"Trials per model: {args.n_trials}")
    print(f"Experiment: {args.experiment_name}")

    # Initialize MLflow
    config = load_config()
    experiment = get_or_create_family_experiment(config, "hyperopt")
    mlflow.set_experiment(experiment.name)
    print(f"\nUsing MLflow experiment: {experiment.name}")

    # Load and preprocess data
    print("\n[1/3] Loading and preprocessing data...")
    train_df, val_df, test_df = load_imdb_dataset()

    X_train_cls, y_train_cls, X_val_cls, y_val_cls, X_test_cls, y_test_cls = (
        None,
        None,
        None,
        None,
        None,
        None,
    )
    train_texts, train_labels, val_texts, val_labels, test_texts, test_labels = (
        None,
        None,
        None,
        None,
        None,
        None,
    )

    if args.mode in ["classical", "both"]:
        X_train_cls, y_train_cls, X_val_cls, y_val_cls, X_test_cls, y_test_cls = (
            preprocess_for_classical(train_df, val_df, test_df)
        )

    if args.mode in ["transformer", "both"]:
        train_texts, train_labels, val_texts, val_labels, test_texts, test_labels = (
            preprocess_for_transformers(train_df, val_df, test_df)
        )

    # Run optimization
    classical_results = {}
    transformer_results = {}

    try:
        if args.mode in ["classical", "both"] and classical_models:
            print(f"\n[2/3] Optimizing classical models: {classical_models}")
            classical_results = run_hyperopt_classical(
                model_types=classical_models,
                X_train=X_train_cls,
                y_train=y_train_cls,
                X_val=X_val_cls,
                y_val=y_val_cls,
                experiment_name=args.experiment_name,
                n_trials=args.n_trials,
                timeout=args.timeout,
                dataset_version=args.dataset_version,
                preprocessing_config=args.preprocessing_config,
            )

        if args.mode in ["transformer", "both"] and transformer_models:
            print(f"\n[2/3] Optimizing transformer models: {transformer_models}")
            transformer_results = run_hyperopt_transformers(
                model_types=transformer_models,
                train_texts=train_texts,
                train_labels=train_labels,
                val_texts=val_texts,
                val_labels=val_labels,
                experiment_name=args.experiment_name,
                n_trials=args.n_trials,
                timeout=args.timeout,
                dataset_version=args.dataset_version,
                preprocessing_config=args.preprocessing_config,
            )
            # For now, we'll skip transformer optimization or we can create a workaround
            # by creating a wrapper that tokenizes inside the objective
            # I'll implement that wrapper if needed.

    except Exception as e:
        print(f"ERROR during optimization: {e}")
        import traceback

        traceback.print_exc()

    # Generate summary
    print("\n[3/3] Optimization complete!")
    print("\n" + "=" * 80)
    print("SUMMARY OF BEST HYPERPARAMETERS")
    print("=" * 80)

    all_results = {**classical_results, **transformer_results}
    summary_data = []

    for model_type, study in all_results.items():
        summary_data.append(
            {
                "model": model_type,
                "best_val_accuracy": float(study.best_value),
                "n_trials": len(study.trials),
                **study.best_params,
            }
        )
        print(f"\n{model_type}:")
        print(f"  Best accuracy: {study.best_value:.4f}")
        for param, value in study.best_params.items():
            print(f"  {param}: {value}")

    # Save summary to CSV
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_path = "../results/hyperopt_optimization_summary.csv"
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        summary_df.to_csv(summary_path, index=False)
        print(f"\nSummary saved to {summary_path}")

        # Log summary to MLflow
        with mlflow.start_run(run_name="hyperopt_summary") as run:
            for _, row in summary_df.iterrows():
                model_name = row["model"]
                mlflow.log_metric(
                    f"{model_name}_best_accuracy", float(row["best_val_accuracy"])
                )
                # Log hyperparameters (all columns except known metadata)
                for col in summary_df.columns:
                    if col not in ["model", "best_val_accuracy", "n_trials"]:
                        mlflow.log_param(f"{model_name}_{col}", row[col])
            mlflow.log_artifact(summary_path)
            print(f"Summary logged to MLflow run: {run.info.run_id}")

    print("\n" + "=" * 80)
    print("HYPERPARAMETER OPTIMIZATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
