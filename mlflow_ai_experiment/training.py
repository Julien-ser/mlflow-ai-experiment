"""
Unified training pipeline for classical and transformer models.
Supports both PyTorch and TensorFlow backends, with features like logging,
checkpointing, early stopping, mixed precision, and comprehensive experiment tracking.
"""

from __future__ import annotations

import importlib.util
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mlflow
import numpy as np
import pandas as pd

from .evaluation import compute_metrics
from .experiment_tracker import (
    get_or_create_family_experiment,
    set_standard_tags,
    log_model_artifact,
    log_predictions,
)

# Local imports
from .models.classical import (
    LogisticRegressionModel,
    RandomForestModel,
    SVMModel,
    XGBoostModel,
)
from .models.transformers import TransformerModel

# Optional PyTorch import
try:
    import torch
    from torch.utils.data import DataLoader

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch: Any = None  # type: ignore
    DataLoader: Any = None  # type: ignore

# Check TensorFlow availability
TF_AVAILABLE = importlib.util.find_spec("tensorflow") is not None

logger = logging.getLogger(__name__)


class Trainer:
    """
    Unified trainer supporting classical ML models and transformer models.
    Handles training loops, logging, checkpointing, early stopping, mixed precision.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        model_type: str = "classical",
        backend: str = "pytorch",
    ) -> None:
        self.config = config
        self.model_type = model_type
        self.backend = backend
        # Device setup
        self.device = None
        if TORCH_AVAILABLE:
            assert torch is not None
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
        self.model: Optional[Any] = None
        self.transformer_model: Optional[Any] = None
        self.optimizer: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.early_stopping_counter = 0
        self.checkpoint_path = Path(
            config.get("checkpoint_dir", "checkpoints")
        )
        self.checkpoint_path.mkdir(parents=True, exist_ok=True)

        # MLflow setup - use experiment_tracker for family-based experiments
        self.mlflow_enabled = config.get("mlflow_tracking", True)
        self.experiment = None
        if self.mlflow_enabled:
            tracking_uri = config.get("mlflow_uri", "sqlite:///mlflow.db")
            mlflow.set_tracking_uri(tracking_uri)

            # Determine model family from model_type
            model_family = (
                "classical" if model_type == "classical" else "transformers"
            )

            # Get or create experiment for this model family
            # Need 'experiments' config; fallback to simple experiment name
            if "experiments" in config:
                self.experiment = get_or_create_family_experiment(
                    config, model_family
                )
                # Set the active experiment to the family experiment
                mlflow.set_experiment(self.experiment.name)
            else:
                # Legacy: use single experiment name
                experiment_name = config.get(
                    "mlflow_experiment_name", model_family
                )
                mlflow.set_experiment(experiment_name)
                print(f"✓ Using experiment: {experiment_name}")

    def _prepare_model(self, model_config: Dict[str, Any]) -> None:
        """
        Prepare model based on type and backend.
        """
        if self.model_type == "classical":
            model_cls = {
                "logistic_regression": LogisticRegressionModel,
                "svm": SVMModel,
                "random_forest": RandomForestModel,
                "xgboost": XGBoostModel,
            }
            if model_config["name"] not in model_cls:
                raise ValueError(
                    f"Unsupported classical model: {model_config['name']}"
                )
            self.model = model_cls[model_config["name"]](
                model_config["params"]
            )
            self.optimizer = None
            # Store model type string for tagging
            self.model_type_str = model_config["name"]
        elif self.model_type == "transformer":
            if not TORCH_AVAILABLE and self.backend == "pytorch":
                raise RuntimeError(
                    "PyTorch is not available for transformer training "
                    "with PyTorch backend"
                )
            # Extract hyperparameters from config
            transformer_params = {
                "model_name": model_config["model_name"],
                "num_labels": model_config.get("num_labels", 2),
                "dropout": model_config.get("dropout", 0.1),
                "max_seq_length": model_config.get("max_seq_length", 512),
                "learning_rate": self.config.get("learning_rate", 2e-5),
                "batch_size": self.config.get("batch_size", 16),
                "num_train_epochs": self.config.get("num_epochs", 3),
                "weight_decay": self.config.get("optimizer", {}).get(
                    "weight_decay", 0.01
                ),
                "warmup_steps": self.config.get("optimizer", {}).get(
                    "warmup_steps", 500
                ),
                "backend": self.backend,
                "early_stopping_patience": self.config.get(
                    "early_stopping_patience", 5
                ),
            }
            transformer = TransformerModel(**transformer_params)
            # Determine model type string for tagging (e.g., 'bert', 'roberta')
            self.model_type_str = transformer._extract_model_type(
                transformer.model_name
            )
            transformer.build_model()
            transformer.load_tokenizer()  # Load tokenizer for later artifact logging
            # Store both the wrapper and the raw model
            self.transformer_model = transformer
            self.model = transformer.model
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def _train_classical(
        self,
        train_dataset: Tuple[np.ndarray, np.ndarray],
        valid_dataset: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    ) -> Dict[str, float]:
        """
        Train a classical model.
        """
        assert self.model is not None
        X_train, y_train = train_dataset
        logger.info("Training classical model...")
        start_time = time.time()
        self.model.fit(X_train, y_train)
        training_duration = time.time() - start_time
        logger.info(f"Training completed in {training_duration:.2f} seconds")

        # Evaluate on training set
        y_pred_train = self.model.predict(X_train)
        train_metrics = compute_metrics(y_train, y_pred_train)
        train_metrics["training_time"] = training_duration

        # Evaluate on validation set if provided
        val_metrics: Dict[str, float] = {}
        if valid_dataset is not None:
            X_val, y_val = valid_dataset
            y_pred_val = self.model.predict(X_val)
            val_metrics = compute_metrics(y_val, y_pred_val)
            val_metrics["validation_time"] = time.time() - start_time

        # Log to MLflow
        if self.mlflow_enabled:
            mlflow.log_metrics(
                {f"train_{k}": v for k, v in train_metrics.items()}
            )
            for k, v in val_metrics.items():
                mlflow.log_metric(f"val_{k}", v)
            # Save model artifact using experiment_tracker
            model_config = self.config.get("model", {})
            model_name = model_config.get("name", "unknown")
            log_model_artifact(
                self.model,
                model_type=model_name,
                framework="sklearn",
                artifact_path="model",
            )

        return {**train_metrics, **val_metrics}

    def _train_transformer(
        self,
        train_dataset: Any,
        valid_dataset: Optional[Any] = None,
    ) -> Dict[str, float]:
        """
        Train a transformer model by delegating to TransformerModel.train().
        """
        # Ensure transformer model is prepared
        if (
            not hasattr(self, "transformer_model")
            or self.transformer_model is None
        ):
            raise RuntimeError("Transformer model not prepared")

        # Build training arguments from config to override defaults
        training_args: Dict[str, Any] = {}
        mp = self.config.get("mixed_precision", False)
        if mp:
            training_args["fp16"] = True

        # Set output_dir to our checkpoint path for unified checkpointing
        training_args["output_dir"] = str(self.checkpoint_path)

        # Configure evaluation and saving strategy
        if valid_dataset is not None:
            training_args["evaluation_strategy"] = "steps"
            training_args["eval_steps"] = 500
            training_args["save_strategy"] = "steps"
            training_args["save_steps"] = 500
            training_args["load_best_model_at_end"] = True
            training_args["metric_for_best_model"] = "eval_accuracy"
            training_args["greater_is_better"] = True
        else:
            training_args["evaluation_strategy"] = "no"
            training_args["save_strategy"] = "epoch"

        # Delegate training to TransformerModel
        train_result = self.transformer_model.train(
            train_dataset=train_dataset,
            eval_dataset=valid_dataset,
            experiment_name=None,  # MLflow handled by outer Trainer
            training_args=training_args,
        )

        # Collect metrics
        metrics: Dict[str, float] = {}
        if train_result is not None:
            metrics["training_loss"] = train_result.training_loss
            metrics["total_steps"] = train_result.global_step
            if hasattr(train_result, "metrics") and train_result.metrics:
                for key, value in train_result.metrics.items():
                    # Convert to float if numeric
                    if isinstance(value, (int, float)):
                        metrics[key] = float(value)

        # Log to MLflow if enabled
        if self.mlflow_enabled:
            # Map metric names to consistent scheme
            if "training_loss" in metrics:
                mlflow.log_metric("train_loss", metrics["training_loss"])
            if "total_steps" in metrics:
                mlflow.log_metric("train_steps", metrics["total_steps"])
            # Any metric starting with 'eval_' becomes 'val_'
            for key in list(metrics.keys()):
                if key.startswith("eval_"):
                    val_key = "val_" + key[5:]
                    mlflow.log_metric(val_key, metrics[key])
                elif key not in ("training_loss", "total_steps"):
                    mlflow.log_metric(key, metrics[key])
            # Log model artifact
            log_model_artifact(
                self.model,
                model_type=self.model_type_str,
                framework="transformers",
                artifact_path="model",
                tokenizer=self.transformer_model.tokenizer,
            )

        return metrics

    def train(
        self,
        train_dataset: Any,
        valid_dataset: Optional[Any] = None,
    ) -> Dict[str, float]:
        """
        Main training entry point.
        """
        # Prepare model
        model_config = self.config.get("model", {})
        self._prepare_model(model_config)

        # Choose training function based on model type
        if self.model_type == "classical":
            train_func = self._train_classical
        elif self.model_type == "transformer":
            train_func = self._train_transformer
        else:
            raise ValueError(f"Unsupported model_type: {self.model_type}")

        # Execute training with or without MLflow run context
        if self.mlflow_enabled:
            with mlflow.start_run() as run:
                mlflow.log_params(self.config)
                # Set standardized tags
                set_standard_tags(
                    model_type=getattr(
                        self, "model_type_str", self.model_type
                    ),
                    dataset_version=self.config.get(
                        "dataset_version", "unknown"
                    ),
                    preprocessing_config=self.config.get(
                        "preprocessing_config", "unknown"
                    ),
                    framework="sklearn"
                    if self.model_type == "classical"
                    else "transformers",
                    run=run,
                )
                metrics = train_func(train_dataset, valid_dataset)
        else:
            metrics = train_func(train_dataset, valid_dataset)

        logger.info("Training completed. Metrics: %s", metrics)
        return metrics

    def evaluate(self, test_dataset: Any) -> Dict[str, float]:
        """
        Evaluate the trained model on a test set.
        """
        if self.model is None:
            raise RuntimeError("Model has not been trained yet")

        predictions_df = None  # To store predictions for logging

        if self.model_type == "classical":
            if not isinstance(test_dataset, tuple):
                raise ValueError(
                    "For classical models, test_dataset must be a tuple (X, y)"
                )
            X_test, y_test = test_dataset
            y_pred = self.model.predict(X_test)
            metrics = compute_metrics(y_test, y_pred)
            predictions_df = pd.DataFrame(
                {
                    "true_label": y_test,
                    "predicted_label": y_pred,
                }
            )
        elif self.model_type == "transformer":
            if not TORCH_AVAILABLE:
                raise RuntimeError("Transformer evaluation requires PyTorch")
            assert torch is not None
            assert DataLoader is not None
            self.model.eval()
            if isinstance(test_dataset, DataLoader):
                loader = test_dataset
            else:
                loader = DataLoader(
                    test_dataset,
                    batch_size=self.config.get("batch_size", 32),
                    shuffle=False,
                )
            all_preds: List[Any] = []
            all_labels: List[Any] = []
            with torch.no_grad():
                for batch in loader:  # type: ignore
                    batch = {k: v.to(self.device) for k, v in batch.items()}
                    outputs = self.model(**batch)
                    logits = outputs.logits
                    preds = torch.argmax(logits, dim=-1)
                    all_preds.extend(preds.cpu().numpy())
                    all_labels.extend(batch["labels"].cpu().numpy())
            metrics = compute_metrics(
                np.array(all_labels), np.array(all_preds)
            )
            predictions_df = pd.DataFrame(
                {
                    "true_label": all_labels,
                    "predicted_label": all_preds,
                }
            )
        else:
            raise ValueError(f"Unsupported model_type: {self.model_type}")

        if self.mlflow_enabled:
            with mlflow.start_run():
                for k, v in metrics.items():
                    mlflow.log_metric(f"test_{k}", v)
                if predictions_df is not None:
                    log_predictions(
                        predictions_df,
                        artifact_path="predictions",
                        filename="predictions.csv",
                    )

        return metrics
