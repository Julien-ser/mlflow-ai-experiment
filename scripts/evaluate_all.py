#!/usr/bin/env python
"""
Batch evaluation script for comparing multiple models.

This script evaluates all models from a given MLflow experiment or a list
of model paths on a common test dataset, computes comprehensive metrics,
logs results consistently, and generates comparison tables.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

from mlflow_ai_experiment.evaluation import (
    compute_metrics,
    measure_inference_latency,
    get_model_size,
    evaluate_model,
)


def load_test_data(test_data_path: str) -> tuple:
    """Load test dataset from numpy files or CSV."""
    test_path = Path(test_data_path)

    if test_path.is_file() and test_path.suffix == ".csv":
        # Load from CSV
        df = pd.read_csv(test_path)
        if "text" in df.columns and "label" in df.columns:
            # Text data - need to handle differently
            return df["text"].tolist(), np.array(df["label"])
        elif "X_test" in df.columns and "y_test" in df.columns:
            # Preprocessed features
            X_test = np.vstack(df["X_test"].values)
            y_test = np.array(df["y_test"])
            return X_test, y_test
        else:
            raise ValueError(
                f"CSV must contain 'text'/'label' or 'X_test'/'y_test' columns"
            )

    # Try numpy files
    X_test_path = test_path / "X_test.npy" if test_path.is_dir() else None
    y_test_path = test_path / "y_test.npy" if test_path.is_dir() else None

    if X_test_path and y_test_path and X_test_path.exists() and y_test_path.exists():
        X_test = np.load(str(X_test_path))
        y_test = np.load(str(y_test_path))
        return X_test, y_test

    raise FileNotFoundError(f"Could not find test data at {test_data_path}")


def get_model_from_mlflow_run(run_id: str, tracking_uri: Optional[str] = None) -> Any:
    """Load a model from an MLflow run."""
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    # Try to load the model artifact
    try:
        # Check if it's a sklearn model
        import mlflow.sklearn as mlflow_sklearn

        model = mlflow_sklearn.load_model(f"runs:/{run_id}/model")
        return model
    except Exception:
        pass

    try:
        # Check if it's a transformers model
        import mlflow.transformers as mlflow_transformers

        model_info = mlflow_transformers.load_model(f"runs:/{run_id}/model")
        # For transformers, return both model and tokenizer
        return model_info
    except Exception:
        pass

    # Generic fallback using MLflow pyfunc
    try:
        model = mlflow.pyfunc.load_model(f"runs:/{run_id}/model")
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load model from run {run_id}: {e}")


def evaluate_all_models(
    test_data_path: str,
    experiment_name: Optional[str] = None,
    run_ids: Optional[List[str]] = None,
    tracking_uri: Optional[str] = None,
    output_dir: str = "comparison_results",
    model_type_hint: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluate multiple models on the same test set.

    Args:
        test_data_path: Path to test data (CSV or directory with X_test.npy, y_test.npy)
        experiment_name: MLflow experiment to query for runs (mutually exclusive with run_ids)
        run_ids: List of specific MLflow run IDs to evaluate
        tracking_uri: MLflow tracking URI
        output_dir: Directory to save comparison results
        model_type_hint: Optional mapping from run_id to model type ('classical' or 'transformer')

    Returns:
        Dictionary mapping model names/run IDs to their evaluation results
    """
    # Setup MLflow
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    # Load test data
    print(f"Loading test data from {test_data_path}...")
    X_test, y_test = load_test_data(test_data_path)
    print(
        f"Test data loaded: X shape={X_test.shape if hasattr(X_test, 'shape') else len(X_test)}, y length={len(y_test)}"
    )

    # Determine which runs to evaluate
    if run_ids is None and experiment_name is not None:
        print(f"Querying runs from experiment: {experiment_name}")
        runs = mlflow.search_runs(
            experiment_ids=[
                mlflow.get_experiment_by_name(experiment_name).experiment_id
            ],
            filter_string="status = 'FINISHED'",
        )
        run_ids = runs["run_id"].tolist()
    elif run_ids is None:
        raise ValueError("Either experiment_name or run_ids must be provided")

    print(f"Found {len(run_ids)} runs to evaluate")

    # Evaluate each model
    results = {}

    for run_id in run_ids:
        print(f"\nEvaluating run {run_id}...")

        try:
            # Get run info
            run = mlflow.get_run(run_id)
            model_type = (
                model_type_hint.get(run_id)
                if model_type_hint
                else run.data.tags.get("model_type", "unknown")
            )
            model_name = run.data.tags.get("mlflow.runName", run_id)

            # Load model
            model = get_model_from_mlflow_run(run_id, tracking_uri)

            # Evaluate
            start_time = time.time()
            if model_type == "transformer":
                # For transformer models, we need special handling
                # The model from mlflow.transformers.load_model returns a pipeline
                # that includes the model and tokenizer, we need to adapt evaluation
                # TODO: Implement proper transformer evaluation in batch context
                print(
                    f"  Skipping transformer model {run_id} - needs custom evaluation logic"
                )
                continue
            else:
                # Classical model evaluation
                metrics = evaluate_model(model, X_test, y_test, log_to_mlflow=False)

            eval_time = time.time() - start_time

            # Store results
            results[run_id] = {
                "run_id": run_id,
                "model_name": model_name,
                "model_type": model_type,
                **metrics,
                "evaluation_time_seconds": eval_time,
            }

            print(
                f"  Results: accuracy={metrics.get('accuracy', 'N/A'):.4f}, "
                f"f1={metrics.get('f1', 'N/A'):.4f}, "
                f"latency={metrics.get('inference_latency_ms', 'N/A'):.2f}ms"
            )

        except Exception as e:
            print(f"  Error evaluating run {run_id}: {e}", file=sys.stderr)
            continue

    if not results:
        print("No models were successfully evaluated.", file=sys.stderr)
        return {}

    # Create comparison DataFrame
    df_results = pd.DataFrame(list(results.values()))

    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / "model_comparison.csv"
    df_results.to_csv(csv_path, index=False)
    print(f"\n✓ Comparison table saved to {csv_path}")

    json_path = output_path / "model_comparison.json"
    df_results.to_json(json_path, orient="records", indent=2)
    print(f"✓ Comparison JSON saved to {json_path}")

    # Log to MLflow as a consolidated comparison run
    print("\nLogging comparison results to MLflow...")
    with mlflow.start_run(run_name="model_comparison") as comparison_run:
        mlflow.log_artifact(str(csv_path), "comparison")
        mlflow.log_artifact(str(json_path), "comparison")

        # Log summary metrics
        for _, row in df_results.iterrows():
            prefix = row["model_name"].replace(" ", "_")
            for metric in [
                "accuracy",
                "precision",
                "recall",
                "f1",
                "inference_latency_ms",
                "model_size_mb",
            ]:
                if metric in row and not pd.isna(row[metric]):
                    mlflow.log_metric(f"{prefix}_{metric}", float(row[metric]))

        print(f"✓ Comparison run logged: {comparison_run.info.run_id}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Batch evaluation of multiple models with comparison table generation."
    )
    parser.add_argument(
        "--test-data",
        required=True,
        help="Path to test data (CSV file or directory with X_test.npy, y_test.npy)",
    )
    parser.add_argument(
        "--experiment-name",
        help="MLflow experiment name containing runs to evaluate",
    )
    parser.add_argument(
        "--run-ids",
        nargs="+",
        help="Specific MLflow run IDs to evaluate (alternative to --experiment-name)",
    )
    parser.add_argument(
        "--tracking-uri",
        default=os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"),
        help="MLflow tracking URI (default: from env or sqlite:///mlflow.db)",
    )
    parser.add_argument(
        "--output-dir",
        default="comparison_results",
        help="Directory to save comparison results (default: comparison_results)",
    )

    args = parser.parse_args()

    if not args.experiment_name and not args.run_ids:
        parser.error("Either --experiment-name or --run-ids must be provided")

    try:
        results = evaluate_all_models(
            test_data_path=args.test_data,
            experiment_name=args.experiment_name,
            run_ids=args.run_ids,
            tracking_uri=args.tracking_uri,
            output_dir=args.output_dir,
        )

        if results:
            print("\n" + "=" * 60)
            print("EVALUATION COMPLETE")
            print(f"Evaluated {len(results)} models")
            print("=" * 60)
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
